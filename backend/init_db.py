#!/usr/bin/env python3
"""Initialize database with default users."""

from database import engine, SessionLocal, Base
from models import User
from auth import get_password_hash


def init_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if admin exists by phone
        admin = db.query(User).filter(User.phone == "13800000000").first()
        if not admin:
            admin_user = User(
                username="管理员",
                hashed_password=get_password_hash("admin123"),
                email="admin@example.com",
                phone="13800000000",
                target_url="https://docs.swanlab.cn/guide_cloud/general/quick-start.html",
                is_admin=True,
                state="inactive",
                owner=None,
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created - Phone: 13800000000, Password: admin123")
        else:
            print("Admin user already exists")

        # Check if demo user exists by phone
        demo = db.query(User).filter(User.phone == "13800000001").first()
        if not demo:
            demo_user = User(
                username="测试选手",
                hashed_password=get_password_hash("demo1234"),
                email="demo@example.com",
                phone="13800000001",
                target_url="https://docs.swanlab.cn/guide_cloud/general/quick-start.html",
                is_admin=False,
                state="inactive",
                instance_id=7764,
                instance_uuid="gghcmwa6-emgm7485",
                owner="管理员",
            )
            db.add(demo_user)
            db.commit()
            print("Demo user created - Phone: 13800000001, Password: demo1234")
        else:
            print("Demo user already exists")

        # List all users
        users = db.query(User).all()
        print(f"\nTotal users in database: {len(users)}")
        for user in users:
            print(f"  - {user.username} (phone: {user.phone}, admin: {user.is_admin})")

    finally:
        db.close()


if __name__ == "__main__":
    init_database()
