from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    target_url = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    state = Column(String, default="inactive")  # active, inactive

    # GPU Instance fields
    instance_id = Column(Integer, nullable=True)
    instance_uuid = Column(String, nullable=True)
    bearer_token = Column(Text, nullable=True)

    # Owner field - which admin created this user (null for admin users)
    owner = Column(String, nullable=True)

    last_login = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())
