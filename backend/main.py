from datetime import timedelta
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from database import engine, get_db, Base, SessionLocal
from models import User
from schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    Token,
    ActionRequest,
    ActionResponse,
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
MAX_USERS_PER_ADMIN = 15


def init_default_users():
    """Initialize default users in database."""
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_user = User(
                username="admin",
                hashed_password=get_password_hash("admin"),
                email="admin@example.com",
                phone="10000000000",
                target_url="https://docs.swanlab.cn/guide_cloud/general/quick-start.html",
                is_admin=True,
                state="inactive",
                owner=None,  # Admin users have no owner
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created: admin/admin")

        # Check if demo user exists
        demo = db.query(User).filter(User.username == "demo").first()
        if not demo:
            demo_user = User(
                username="demo",
                hashed_password=get_password_hash("demo1234"),
                email="demo@example.com",
                phone="10000000001",
                target_url="https://docs.swanlab.cn/guide_cloud/general/quick-start.html",
                is_admin=False,
                state="inactive",
                instance_id=7764,
                instance_uuid="gghcmwa6-emgm7485",
                owner="admin",  # Created by admin
            )
            db.add(demo_user)
            db.commit()
            print("Demo user created: demo/demo1234")
    except Exception as e:
        print(f"Error initializing users: {e}")
        db.rollback()
    finally:
        db.close()


# Initialize default users on startup
@app.on_event("startup")
async def startup_event():
    init_default_users()


# Health check endpoint
@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    return {"status": "healthy", "user_count": user_count}


# Auth endpoints
@app.post("/api/auth/login", response_model=Token)
async def login(form_data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Update last login
    user.last_login = func.now()
    db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
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
            detail=f"Maximum user limit reached. You can only create up to {MAX_USERS_PER_ADMIN} users.",
        )

    # Check if username exists
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Check if email exists (if provided)
    if user.email:
        existing_email = db.query(User).filter(User.email == user.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

    # Check if phone exists (if provided)
    if user.phone:
        existing_phone = db.query(User).filter(User.phone == user.phone).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already exists",
            )

    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        email=user.email,
        phone=user.phone,
        target_url=user.target_url,
        is_admin=user.is_admin,
        state="inactive",
        instance_id=user.instance_id,
        instance_uuid=user.instance_uuid,
        bearer_token=user.bearer_token,
        owner=current_user.username,  # Set owner to current admin
    )
    db.add(new_user)
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
            detail="User not found",
        )

    # Check if admin owns this user or it's themselves
    if user.owner != current_user.username and user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit users you created",
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
                detail="Username already exists",
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
                    detail="Email already exists",
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
                    detail="Phone number already exists",
                )
        user.phone = user_update.phone

    if user_update.password is not None:
        user.hashed_password = get_password_hash(user_update.password)

    if user_update.target_url is not None:
        user.target_url = user_update.target_url

    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
