from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend._core.deps import Principal, get_current_principal, require_platform_admin
from backend.db import get_db
from backend.notifications.schemas import NotificationOut
from backend.notifications.services import list_for_user, mark_read, run_expiry_check

router = APIRouter(tags=["notifications"])


@router.get("/api/notifications", response_model=list[NotificationOut])
def my_notifications(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    return list_for_user(db, principal.user.id)


@router.post("/api/notifications/read")
def read_notifications(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    return {"updated": mark_read(db, principal.user.id)}


@router.post("/api/notifications/run-expiry-check")
def run_check(_principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return {"created": run_expiry_check(db)}
