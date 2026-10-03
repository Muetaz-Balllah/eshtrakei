from sqlalchemy import select

from backend._core.security import hash_password
from backend.auth.models import User
from backend.config import get_settings
from backend.db import SessionLocal
from backend.enums import UserRole
from backend.utils import utc_now


def seed_admin() -> None:
    settings = get_settings()
    if not settings.platform_admin_password:
        raise SystemExit("PLATFORM_ADMIN_PASSWORD is empty")
    db = SessionLocal()
    try:
        email = settings.platform_admin_email.lower()
        existing = db.scalar(select(User).where(User.email == email))
        if existing is not None:
            print(f"Platform admin already exists: {email}")
            return
        db.add(
            User(
                full_name="مدير المنصة",
                email=email,
                password_hash=hash_password(settings.platform_admin_password),
                role=UserRole.platform_admin,
                is_active=True,
                created_at=utc_now(),
            )
        )
        db.commit()
        print(f"Platform admin created: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
