from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class GpuInstance(Base):
    """GPU instances for competition users.

    Instances are manually added by admin.
    Each instance can only be assigned to one user at a time.
    """
    __tablename__ = "gpu_instances"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, unique=True, nullable=False, index=True)  # GPUFree instance ID
    instance_uuid = Column(String, unique=True, nullable=False)  # GPUFree instance UUID
    nickname = Column(String, nullable=False)  # Display name, e.g., 'haidian-BOB专用2'
    vnc_url = Column(String, nullable=True)  # Target URL for this instance

    # Assignment tracking
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    plain_password = Column(String, nullable=True)  # Store plaintext for admin visibility
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

    # Heartbeat for inactivity detection
    last_heartbeat = Column(DateTime, nullable=True)

    last_login = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())
