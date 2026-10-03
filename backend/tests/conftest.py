import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["PLATFORM_ADMIN_EMAIL"] = "admin@eshtrakei.local"
os.environ["PLATFORM_ADMIN_PASSWORD"] = "phase0-admin-pass"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"

import fakeredis
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from backend._core.deps import require_platform_admin
from backend._core.redis_client import set_redis_client
from backend._core.security import hash_password
from backend.auth.models import User
from backend.config import get_settings
from backend.db import Base, SessionLocal, engine
from backend.enums import UserRole
from backend.main import create_app
from backend.utils import utc_now

get_settings.cache_clear()


@pytest.fixture()
def client():
    set_redis_client(fakeredis.FakeRedis(decode_responses=True))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    app = create_app()

    @app.get("/api/_phase0/admin-probe")
    def admin_probe(_principal=Depends(require_platform_admin)):
        return {"ok": True}

    db = SessionLocal()
    db.add(
        User(
            full_name="مدير المنصة",
            email="admin@eshtrakei.local",
            password_hash=hash_password("phase0-admin-pass"),
            role=UserRole.platform_admin,
            is_active=True,
            created_at=utc_now(),
        )
    )
    db.add(
        User(
            full_name="زبون تجريبي",
            email="client@eshtrakei.local",
            password_hash=hash_password("phase0-client-pass"),
            role=UserRole.client,
            is_active=True,
            created_at=utc_now(),
        )
    )
    db.commit()
    db.close()
    with TestClient(app) as test_client:
        yield test_client
