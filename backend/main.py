import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from database import engine, get_db, Base, SessionLocal
from models import User, GpuInstance
from schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    ActionRequest,
    ActionResponse,
    GpuInstanceCreate,
    GpuInstanceUpdate,
    GpuInstanceResponse,
)
from auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from control_gpufree import GPUFreeClient

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Portal API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
MAX_USERS_PER_ADMIN = 128
INACTIVITY_TIMEOUT_MINUTES = 180  # Auto-stop instance after 180 minutes (3 hours) of inactivity
INACTIVITY_CHECK_INTERVAL = 60  # Check for inactive users every 60 seconds
DAILY_SHUTDOWN_HOUR = 2  # Shutdown all instances at 2 AM Beijing time
BEIJING_TZ = ZoneInfo("Asia/Shanghai")  # Beijing timezone


def init_default_users():
    """Initialize default admin user in database."""
    db = SessionLocal()
    default_password = "DongSheng2025#"
    try:
        # Check if admin exists by phone (login is by phone now)
        admin = db.query(User).filter(User.phone == "13800000000").first()
        if admin:
            # Admin exists - ensure password is synced
            # Always update both hashed and plain password to ensure they match
            admin.hashed_password = get_password_hash(default_password)
            admin.plain_password = default_password
            admin.username = "管理员"
            db.commit()
            print(f"Admin user synced - Phone: 13800000000, Password: {default_password}")
        else:
            # Check if old admin exists (by username "admin" or "管理员") and update it
            old_admin = db.query(User).filter(
                (User.username == "admin") | (User.username == "管理员")
            ).filter(User.is_admin == True).first()
            if old_admin:
                old_admin.phone = "13800000000"
                old_admin.hashed_password = get_password_hash(default_password)
                old_admin.plain_password = default_password
                old_admin.username = "管理员"
                db.commit()
                print(f"Admin user updated with phone: 13800000000, password: {default_password}")
            else:
                admin_user = User(
                    username="管理员",
                    hashed_password=get_password_hash(default_password),
                    plain_password=default_password,
                    email="admin@example.com",
                    phone="13800000000",
                    target_url="https://docs.swanlab.cn/guide_cloud/general/quick-start.html",
                    is_admin=True,
                    state="inactive",
                    owner=None,  # Admin users have no owner
                )
                db.add(admin_user)
                db.commit()
                print(f"Admin user created - Phone: 13800000000, Password: {default_password}")
    except Exception as e:
        print(f"Error initializing users: {e}")
        db.rollback()
    finally:
        db.close()


# Background task to check for inactive users and stop their instances
async def check_inactive_users():
    """Background task that runs periodically to stop inactive user instances."""
    logger.info(f"[INACTIVITY] Background task started. Check interval: {INACTIVITY_CHECK_INTERVAL}s, Timeout: {INACTIVITY_TIMEOUT_MINUTES} min")

    while True:
        await asyncio.sleep(INACTIVITY_CHECK_INTERVAL)
        logger.info("[INACTIVITY] Running inactivity check...")

        db = SessionLocal()
        try:
            now = datetime.utcnow()
            threshold = now - timedelta(minutes=INACTIVITY_TIMEOUT_MINUTES)
            logger.info(f"[INACTIVITY] Current UTC time: {now.isoformat()}, Threshold: {threshold.isoformat()}")

            # First, log all active users with their heartbeat status
            all_active_users = db.query(User).filter(
                User.state == "active",
                User.instance_id.isnot(None)
            ).all()

            logger.info(f"[INACTIVITY] Found {len(all_active_users)} active users with instances")

            for user in all_active_users:
                if user.last_heartbeat:
                    age_seconds = (now - user.last_heartbeat).total_seconds()
                    logger.info(f"[INACTIVITY] User '{user.username}': last_heartbeat={user.last_heartbeat.isoformat()}, age={age_seconds:.1f}s ({age_seconds/60:.1f} min)")
                else:
                    logger.info(f"[INACTIVITY] User '{user.username}': last_heartbeat=None (no heartbeat received yet)")

            # Find active users whose last heartbeat is older than threshold
            inactive_users = db.query(User).filter(
                User.state == "active",
                User.instance_id.isnot(None),
                User.last_heartbeat.isnot(None),
                User.last_heartbeat < threshold
            ).all()

            logger.info(f"[INACTIVITY] Found {len(inactive_users)} inactive users to stop")

            for user in inactive_users:
                try:
                    age_seconds = (now - user.last_heartbeat).total_seconds()
                    logger.info(f"[INACTIVITY] Stopping instance for user '{user.username}' (inactive for {age_seconds/60:.1f} min)")

                    # Create GPUFree client
                    if user.bearer_token:
                        client = GPUFreeClient(bearer_token=user.bearer_token)
                    else:
                        client = GPUFreeClient()

                    # Stop the instance
                    success, msg = client.stop_instance(
                        instance_id=user.instance_id,
                        instance_uuid=user.instance_uuid
                    )

                    if success:
                        user.state = "inactive"
                        user.last_heartbeat = None
                        db.commit()
                        logger.info(f"[INACTIVITY] Successfully auto-stopped instance for user: {user.username}")
                    else:
                        logger.error(f"[INACTIVITY] Failed to auto-stop instance for user {user.username}: {msg}")

                except Exception as e:
                    logger.error(f"[INACTIVITY] Error stopping instance for user {user.username}: {e}")

        except Exception as e:
            logger.error(f"[INACTIVITY] Error in inactivity check: {e}")
        finally:
            db.close()


# Background task to shutdown all instances at 2 AM daily
async def daily_shutdown_task():
    """Background task that shuts down all active instances at 2 AM Beijing time."""
    logger.info(f"[DAILY_SHUTDOWN] Background task started. Scheduled shutdown at {DAILY_SHUTDOWN_HOUR}:00 Beijing time")

    while True:
        now = datetime.now(BEIJING_TZ)  # Beijing time
        # Calculate next 2 AM Beijing time
        next_shutdown = now.replace(hour=DAILY_SHUTDOWN_HOUR, minute=0, second=0, microsecond=0)
        if now >= next_shutdown:
            # If we're past 2 AM today, schedule for tomorrow
            next_shutdown += timedelta(days=1)

        # Calculate seconds until next shutdown
        seconds_until_shutdown = (next_shutdown - now).total_seconds()
        logger.info(f"[DAILY_SHUTDOWN] Current Beijing time: {now.strftime('%Y-%m-%d %H:%M:%S')}, Next shutdown at {next_shutdown.strftime('%Y-%m-%d %H:%M:%S')} Beijing time, sleeping for {seconds_until_shutdown/3600:.1f} hours")

        await asyncio.sleep(seconds_until_shutdown)

        # Time to shutdown all instances
        logger.info("[DAILY_SHUTDOWN] Starting daily shutdown of all instances...")
        db = SessionLocal()
        try:
            # Find all users with assigned instances (regardless of state)
            users_with_instances = db.query(User).filter(
                User.instance_id.isnot(None)
            ).all()

            logger.info(f"[DAILY_SHUTDOWN] Found {len(users_with_instances)} instances to stop")

            stopped_count = 0
            failed_count = 0

            for user in users_with_instances:
                try:
                    logger.info(f"[DAILY_SHUTDOWN] Stopping instance for user '{user.username}'")

                    # Create GPUFree client
                    if user.bearer_token:
                        client = GPUFreeClient(bearer_token=user.bearer_token)
                    else:
                        client = GPUFreeClient()

                    # Stop the instance
                    success, msg = client.stop_instance(
                        instance_id=user.instance_id,
                        instance_uuid=user.instance_uuid
                    )

                    if success:
                        user.state = "inactive"
                        user.last_heartbeat = None
                        db.commit()
                        stopped_count += 1
                        logger.info(f"[DAILY_SHUTDOWN] Successfully stopped instance for user: {user.username}")
                    else:
                        failed_count += 1
                        logger.error(f"[DAILY_SHUTDOWN] Failed to stop instance for user {user.username}: {msg}")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"[DAILY_SHUTDOWN] Error stopping instance for user {user.username}: {e}")

            logger.info(f"[DAILY_SHUTDOWN] Daily shutdown complete. Stopped: {stopped_count}, Failed: {failed_count}")

        except Exception as e:
            logger.error(f"[DAILY_SHUTDOWN] Error in daily shutdown: {e}")
        finally:
            db.close()

        # Sleep a bit to avoid triggering again immediately
        await asyncio.sleep(60)


# Initialize default users on startup
@app.on_event("startup")
async def startup_event():
    init_default_users()
    # Start background task for inactivity detection
    logger.info("[STARTUP] Starting inactivity detection background task...")
    asyncio.create_task(check_inactive_users())
    # Start background task for daily shutdown at 2 AM
    logger.info("[STARTUP] Starting daily shutdown background task...")
    asyncio.create_task(daily_shutdown_task())
    logger.info("[STARTUP] Backend started successfully")


# Health check endpoint
@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    return {"status": "healthy", "user_count": user_count}


# Auth endpoints
@app.post("/api/auth/login", response_model=Token)
async def login(form_data: UserLogin, db: Session = Depends(get_db)):
    # Use phone number for login (form_data.username contains phone)
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Update last login
    user.last_login = func.now()
    db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.phone}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# User management endpoints (Admin only)
@app.get("/api/users", response_model=List[UserResponse])
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get users created by the current admin (not other admins' users)"""
    # Admin can only see users they created (owner = current admin's username)
    # Plus they can see themselves
    users = db.query(User).filter(
        (User.owner == current_user.username) | (User.id == current_user.id)
    ).all()
    return users


@app.get("/api/users/count")
async def get_user_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get count of users created by the current admin"""
    count = db.query(User).filter(User.owner == current_user.username).count()
    return {"count": count, "max": MAX_USERS_PER_ADMIN}


@app.post("/api/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    # Check if admin has reached max user limit
    user_count = db.query(User).filter(User.owner == current_user.username).count()
    if user_count >= MAX_USERS_PER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"已达到用户上限，最多只能创建 {MAX_USERS_PER_ADMIN} 个用户",
        )

    # Check if username exists
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    # Check if email exists (if provided)
    if user.email:
        existing_email = db.query(User).filter(User.email == user.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在",
            )

    # Check if phone exists
    if user.phone:
        existing_phone = db.query(User).filter(User.phone == user.phone).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="手机号已存在",
            )

    # Get GPU instance if selected (for non-admin users)
    instance_id = None
    instance_uuid = None
    gpu_instance = None
    target_url = user.target_url

    if not user.is_admin and user.gpu_instance_id:
        gpu_instance = db.query(GpuInstance).filter(
            GpuInstance.id == user.gpu_instance_id
        ).first()
        if not gpu_instance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="选择的GPU实例不存在",
            )
        if gpu_instance.assigned_user_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="选择的GPU实例已被分配给其他用户",
            )
        instance_id = gpu_instance.instance_id
        instance_uuid = gpu_instance.instance_uuid
        # Use instance's vnc_url if available
        if gpu_instance.vnc_url:
            target_url = gpu_instance.vnc_url

    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        plain_password=user.password,  # Store plaintext for admin visibility
        email=user.email,
        phone=user.phone,
        target_url=target_url,
        is_admin=user.is_admin,
        state="inactive",
        instance_id=instance_id,
        instance_uuid=instance_uuid,
        bearer_token=user.bearer_token,
        owner=current_user.username,  # Set owner to current admin
    )
    db.add(new_user)
    db.flush()  # Get new_user.id

    # Mark instance as assigned (if selected)
    if gpu_instance:
        gpu_instance.assigned_user_id = new_user.id

    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    # Check if admin owns this user or it's themselves
    if user.owner != current_user.username and user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view users you created",
        )
    return user


@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # Check if admin owns this user or it's themselves
    if user.owner != current_user.username and user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能编辑自己创建的用户",
        )

    if user_update.username is not None:
        # Check if new username already exists
        existing = (
            db.query(User)
            .filter(User.username == user_update.username, User.id != user_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在",
            )
        user.username = user_update.username

    if user_update.email is not None:
        # Check if new email already exists
        if user_update.email:
            existing = (
                db.query(User)
                .filter(User.email == user_update.email, User.id != user_id)
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已存在",
                )
        user.email = user_update.email

    if user_update.phone is not None:
        # Check if new phone already exists
        if user_update.phone:
            existing = (
                db.query(User)
                .filter(User.phone == user_update.phone, User.id != user_id)
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="手机号已存在",
                )
        user.phone = user_update.phone

    if user_update.password is not None:
        user.hashed_password = get_password_hash(user_update.password)
        user.plain_password = user_update.password  # Update plaintext as well

    if user_update.target_url is not None:
        user.target_url = user_update.target_url

    # is_admin cannot be changed after creation (read-only)
    # if user_update.is_admin is not None:
    #     user.is_admin = user_update.is_admin

    if user_update.state is not None:
        user.state = user_update.state

    if user_update.instance_id is not None:
        user.instance_id = user_update.instance_id

    if user_update.instance_uuid is not None:
        user.instance_uuid = user_update.instance_uuid

    if user_update.bearer_token is not None:
        user.bearer_token = user_update.bearer_token

    db.commit()
    db.refresh(user)
    return user


@app.delete("/api/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )

    # Check if admin owns this user
    if user.owner != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete users you created",
        )

    # Release the GPU instance (clear assigned_user_id)
    if user.instance_id:
        gpu_instance = db.query(GpuInstance).filter(
            GpuInstance.instance_id == user.instance_id
        ).first()
        if gpu_instance:
            gpu_instance.assigned_user_id = None

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


# Portal action endpoints
@app.post("/api/portal/action", response_model=ActionResponse)
async def portal_action(
    action: ActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Handle start/stop actions using GPUFree API.
    """
    if action.action not in ["start", "stop"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Use 'start' or 'stop'",
        )

    # Check if user has instance configured
    if not current_user.instance_id or not current_user.instance_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No GPU instance configured for this user",
        )

    try:
        # Create GPUFree client with user's bearer token if available
        if current_user.bearer_token:
            client = GPUFreeClient(bearer_token=current_user.bearer_token)
        else:
            client = GPUFreeClient()

        if action.action == "start":
            success, msg = client.start_instance(
                instance_id=current_user.instance_id,
                instance_uuid=current_user.instance_uuid
            )
        else:
            success, msg = client.stop_instance(
                instance_id=current_user.instance_id,
                instance_uuid=current_user.instance_uuid
            )

        if success:
            # Update user state
            new_state = "active" if action.action == "start" else "inactive"
            current_user.state = new_state
            db.commit()

            return ActionResponse(
                success=True,
                message=f"Successfully executed {action.action} action",
                target_url=current_user.target_url if action.action == "start" else None,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to {action.action} instance: {msg}",
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute action: {str(e)}",
        )


@app.get("/api/portal/target-url")
async def get_target_url(current_user: User = Depends(get_current_user)):
    """Get the target URL for the current user"""
    return {"target_url": current_user.target_url, "state": current_user.state}


@app.post("/api/portal/heartbeat")
async def heartbeat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update user's last heartbeat timestamp.
    Frontend should call this every 30-60 seconds while user is active.
    If no heartbeat received for INACTIVITY_TIMEOUT_MINUTES, instance will be auto-stopped.
    """
    current_user.last_heartbeat = datetime.utcnow()
    db.commit()
    logger.info(f"[HEARTBEAT] Received from user '{current_user.username}' at {current_user.last_heartbeat.isoformat()} UTC")
    return {
        "status": "ok",
        "last_heartbeat": current_user.last_heartbeat.isoformat(),
        "timeout_minutes": INACTIVITY_TIMEOUT_MINUTES
    }


@app.get("/api/portal/query-instance")
async def query_instance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Query the current status of the user's GPU instance.
    Returns status code: 3 = running, 5 = stopped
    """
    # Check if user has instance configured
    if not current_user.instance_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No GPU instance configured for this user",
        )

    try:
        # Create GPUFree client with user's bearer token if available
        if current_user.bearer_token:
            client = GPUFreeClient(bearer_token=current_user.bearer_token)
        else:
            client = GPUFreeClient()

        status_code, jupyter_url = client.get_instance_status(current_user.instance_id)

        if status_code is not None:
            # Update user state based on instance status
            if status_code == 3:  # Running
                current_user.state = "active"
            elif status_code == 5:  # Stopped
                current_user.state = "inactive"
            db.commit()

            return {
                "status": status_code,
                "is_running": status_code == 3,
                "jupyter_url": jupyter_url,
                "target_url": current_user.target_url,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Instance not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query instance: {str(e)}",
        )


# GPU Instance management endpoints (Admin only)
@app.get("/api/instances")
async def get_instances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get all GPU instances with assigned username."""
    instances = db.query(GpuInstance).all()
    result = []
    for inst in instances:
        inst_dict = {
            "id": inst.id,
            "instance_id": inst.instance_id,
            "instance_uuid": inst.instance_uuid,
            "nickname": inst.nickname,
            "vnc_url": inst.vnc_url,
            "assigned_user_id": inst.assigned_user_id,
            "assigned_username": None,
            "created_at": inst.created_at,
            "updated_at": inst.updated_at,
        }
        # Get assigned username if exists
        if inst.assigned_user_id:
            user = db.query(User).filter(User.id == inst.assigned_user_id).first()
            if user:
                inst_dict["assigned_username"] = user.username
        result.append(inst_dict)
    return result


@app.get("/api/instances/available")
async def get_available_instances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get unassigned GPU instances for dropdown selection."""
    instances = db.query(GpuInstance).filter(
        GpuInstance.assigned_user_id == None
    ).all()
    return [
        {
            "id": inst.id,
            "instance_id": inst.instance_id,
            "nickname": inst.nickname,
            "vnc_url": inst.vnc_url,
        }
        for inst in instances
    ]


@app.post("/api/instances", response_model=GpuInstanceResponse)
async def create_instance(
    instance: GpuInstanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Manually add a new GPU instance.

    The instance_id is automatically fetched from GPUFree API using the uuid.
    """
    # Check if instance_uuid already exists
    existing_uuid = db.query(GpuInstance).filter(
        GpuInstance.instance_uuid == instance.instance_uuid
    ).first()
    if existing_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="实例UUID已存在",
        )

    # Query GPUFree API to get instance_id from uuid
    try:
        client = GPUFreeClient()
        gpu_instance_data = client.get_instance_by_uuid(instance.instance_uuid)
        if not gpu_instance_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"在GPUFree中找不到UUID为 '{instance.instance_uuid}' 的实例，请检查UUID是否正确",
            )
        instance_id = gpu_instance_data.get("webide_instance_id")
        if not instance_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法从GPUFree获取实例ID",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询GPUFree API失败: {str(e)}",
        )

    # Check if instance_id already exists
    existing = db.query(GpuInstance).filter(
        GpuInstance.instance_id == instance_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"实例ID {instance_id} 已存在",
        )

    new_instance = GpuInstance(
        instance_id=instance_id,
        instance_uuid=instance.instance_uuid,
        nickname=instance.nickname,
        vnc_url=instance.vnc_url,
    )
    db.add(new_instance)
    db.commit()
    db.refresh(new_instance)
    return new_instance


@app.put("/api/instances/{id}", response_model=GpuInstanceResponse)
async def update_instance(
    id: int,
    instance_update: GpuInstanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update a GPU instance."""
    instance = db.query(GpuInstance).filter(GpuInstance.id == id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="实例不存在",
        )

    if instance_update.instance_id is not None:
        # Check uniqueness
        existing = db.query(GpuInstance).filter(
            GpuInstance.instance_id == instance_update.instance_id,
            GpuInstance.id != id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="实例ID已存在",
            )
        instance.instance_id = instance_update.instance_id

    if instance_update.instance_uuid is not None:
        existing = db.query(GpuInstance).filter(
            GpuInstance.instance_uuid == instance_update.instance_uuid,
            GpuInstance.id != id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="实例UUID已存在",
            )
        instance.instance_uuid = instance_update.instance_uuid

    if instance_update.nickname is not None:
        instance.nickname = instance_update.nickname

    if instance_update.vnc_url is not None:
        instance.vnc_url = instance_update.vnc_url

    db.commit()
    db.refresh(instance)
    return instance


@app.delete("/api/instances/{id}")
async def delete_instance(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete a GPU instance. Cannot delete if assigned to a user."""
    instance = db.query(GpuInstance).filter(GpuInstance.id == id).first()
    if not instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="实例不存在",
        )

    if instance.assigned_user_id is not None:
        # Get username for better error message
        user = db.query(User).filter(User.id == instance.assigned_user_id).first()
        username = user.username if user else f"ID:{instance.assigned_user_id}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法删除已分配给用户 '{username}' 的实例，请先删除该用户",
        )

    db.delete(instance)
    db.commit()
    return {"message": "实例删除成功"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
