from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str
    target_url: str
    is_admin: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    target_url: Optional[str] = None
    is_admin: Optional[bool] = None
    state: Optional[str] = None


class UserResponse(UserBase):
    id: int
    state: str
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
