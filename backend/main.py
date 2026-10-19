from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend._core.object_storage import get_object, object_storage_enabled
from backend._core.redis_client import get_redis
from backend.banners.routes import router as banners_router
from backend.coverage.routes import router as coverage_router
from backend.wallets.routes import router as wallets_router
from backend.auth.routes import router as auth_router
from backend.companies.routes import router as companies_router
from backend.complaints.routes import router as complaints_router
from backend.coupons.routes import router as coupons_router
from backend.invoices.routes import router as invoices_router
from backend.notifications.routes import router as notifications_router
from backend.packages.routes import router as packages_router
from backend.reports.routes import router as reports_router
from backend.settings.routes import router as settings_router
from backend.subscriptions.routes import router as subscriptions_router
from backend.errors import AppError
from backend.config import get_settings
from backend.db import SessionLocal, get_db
from backend.middleware import register_middleware
from backend.notifications.services import run_expiry_check


def _expiry_job() -> None:
    db = SessionLocal()
    try:
        run_expiry_check(db)
    finally:
        db.close()


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    scheduler = BackgroundScheduler(timezone="Africa/Tripoli")
    scheduler.add_job(_expiry_job, "cron", hour=8, minute=0)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Eshtrakei", lifespan=_lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_middleware(app)
    app.include_router(auth_router)
    app.include_router(companies_router)
    app.include_router(packages_router)
    app.include_router(coupons_router)
    app.include_router(subscriptions_router)
    app.include_router(invoices_router)
    app.include_router(notifications_router)
    app.include_router(complaints_router)
    app.include_router(reports_router)
    app.include_router(settings_router)
    app.include_router(wallets_router)
    app.include_router(banners_router)
    app.include_router(coverage_router)

    @app.get("/api/media/{folder}/{filename}")
    def media(folder: str, filename: str) -> Response:
        if folder not in {"logos", "banners", "avatars"} or "/" in filename or "\\" in filename or ".." in filename:
            raise AppError(404, "not_found", "الملف غير موجود")
        path = Path("backend/storage") / folder / filename
        if path.is_file():
            return FileResponse(path)
        if object_storage_enabled():
            content = get_object(f"{folder}/{filename}")
            if content is not None:
                media_type = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}.get(path.suffix, "application/octet-stream")
                return Response(content, media_type=media_type)
        raise AppError(404, "not_found", "الملف غير موجود")

    @app.get("/api/health")
    def health(db: Session = Depends(get_db)) -> dict:
        db_ok = False
        redis_ok = False
        try:
            db.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
        try:
            redis_ok = bool(get_redis().ping())
        except RedisError:
            redis_ok = False
        return {"database": db_ok, "redis": redis_ok}

    return app


app = create_app()
