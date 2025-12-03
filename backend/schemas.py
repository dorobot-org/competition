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


class UserCreate(UserBase):
    password: str


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
