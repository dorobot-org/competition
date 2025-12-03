from datetime import timedelta
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import httpx

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
                target_url="https://docs.swanlab.cn/guide_cloud/general/quick-start.html",
                is_admin=True,
                state="inactive",
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
                target_url="https://docs.swanlab.cn/guide_cloud/general/quick-start.html",
                is_admin=False,
                state="inactive",
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
    users = db.query(User).all()
    return users


@app.post("/api/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    # Check if username exists
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    new_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        target_url=user.target_url,
        is_admin=user.is_admin,
        state="inactive",
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

    if user_update.password is not None:
        user.hashed_password = get_password_hash(user_update.password)

    if user_update.target_url is not None:
        user.target_url = user_update.target_url

    if user_update.is_admin is not None:
        user.is_admin = user_update.is_admin

    if user_update.state is not None:
        user.state = user_update.state

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
    Handle start/stop actions.
    This simulates calling a third-party API.
    """
    if action.action not in ["start", "stop"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Use 'start' or 'stop'",
        )

    # Simulate third-party API call
    # In production, replace with actual API endpoint
    try:
        # Simulating API call to third-party server
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://third-party-api.example.com/action",
        #         json={"user_id": current_user.id, "action": action.action}
        #     )

        # Update user state
        new_state = "active" if action.action == "start" else "inactive"
        current_user.state = new_state
        db.commit()

        return ActionResponse(
            success=True,
            message=f"Successfully executed {action.action} action",
            target_url=current_user.target_url if action.action == "start" else None,
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
