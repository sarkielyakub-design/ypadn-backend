import os

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash


def create_default_admin():
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not password:
        print("ℹ️ ADMIN_USERNAME/ADMIN_PASSWORD not configured; default admin creation skipped.")
        return

    db: Session = SessionLocal()

    try:
        admin = db.query(User).filter(User.username == username).first()

        if not admin:
            admin = User(
                username=username,
                hashed_password=get_password_hash(password),
                role="admin"
            )
            db.add(admin)
            db.commit()
            print("✅ YPADN default admin created")
        else:
            print("✅ YPADN admin already exists")
    finally:
        db.close()
