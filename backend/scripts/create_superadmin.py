"""
One-time superadmin bootstrap script.

Run from the backend root:
    python scripts/create_superadmin.py

Creates admin@voxen.ai with password VoxenAdmin2026! and
is_superadmin=True, is_active=True.

If the email already exists, it is left untouched (no password reset).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.auth.security import hash_password


SUPERADMIN_EMAIL = "admin@voxen.ai"
SUPERADMIN_PASSWORD = "VoxenAdmin2026!"


def create_superadmin() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == SUPERADMIN_EMAIL).first()
        if existing:
            print(f"Superadmin already exists: {SUPERADMIN_EMAIL}")
            return

        admin = User(
            email=SUPERADMIN_EMAIL,
            username="admin",
            hashed_password=hash_password(SUPERADMIN_PASSWORD),
            role=UserRole.ADMIN,
            is_superadmin=True,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("Superadmin created successfully")
        print(f"   Email:    {SUPERADMIN_EMAIL}")
        print(f"   Password: {SUPERADMIN_PASSWORD}")
        print("   Change this password immediately after first login!")
    finally:
        db.close()


if __name__ == "__main__":
    create_superadmin()
