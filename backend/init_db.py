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
                owner=None,
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created: admin/admin")
        else:
            print("Admin user already exists")

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
                owner="admin",
            )
            db.add(demo_user)
            db.commit()
            print("Demo user created: demo/demo1234")
        else:
            print("Demo user already exists")

        # List all users
        users = db.query(User).all()
        print(f"\nTotal users in database: {len(users)}")
        for user in users:
            print(f"  - {user.username} (admin: {user.is_admin}, owner: {user.owner})")

    finally:
        db.close()


if __name__ == "__main__":
    init_database()
