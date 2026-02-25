from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    target_url: str
    is_admin: bool = False
    instance_id: Optional[int] = None
    instance_uuid: Optional[str] = None
    bearer_token: Optional[str] = None


class UserCreate(BaseModel):
    """User creation - select GPU instance from dropdown."""
    username: str
    password: str
    email: Optional[str] = None
    phone: Optional[str] = None
    target_url: str = "https://docs.swanlab.cn/guide_cloud/general/quick-start.html"
    is_admin: bool = False
    bearer_token: Optional[str] = None
    gpu_instance_id: Optional[int] = None  # ID from gpu_instances table (not instance_id)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    target_url: Optional[str] = None
    is_admin: Optional[bool] = None
    state: Optional[str] = None
    instance_id: Optional[int] = None
    instance_uuid: Optional[str] = None
    bearer_token: Optional[str] = None


class UserResponse(UserBase):
    id: int
    state: str
    owner: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class ActionRequest(BaseModel):
    action: str  # "start" or "stop"


class ActionResponse(BaseModel):
    success: bool
    message: str
    target_url: Optional[str] = None


class GpuInstanceCreate(BaseModel):
    """Create a new GPU instance manually.

    instance_id is fetched automatically from GPUFree API using the uuid.
    """
    instance_uuid: str
    nickname: str
    vnc_url: Optional[str] = None


class GpuInstanceUpdate(BaseModel):
    """Update GPU instance fields."""
    instance_id: Optional[int] = None
    instance_uuid: Optional[str] = None
    nickname: Optional[str] = None
    vnc_url: Optional[str] = None


class GpuInstanceResponse(BaseModel):
    id: int
    instance_id: int
    instance_uuid: str
    nickname: str
    vnc_url: Optional[str] = None
    assigned_user_id: Optional[int] = None
    assigned_username: Optional[str] = None  # For display
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
