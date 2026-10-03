from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend._core.deps import Principal, get_current_principal, require_platform_admin
from backend.db import get_db
from backend.settings.schemas import SettingsOut, SettingsUpdate
from backend.settings.services import get_settings_view, support_email, update_settings

router = APIRouter(tags=["settings"])


@router.get("/api/settings/support-email")
def public_support_email(_principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    return {"support_email": support_email(db)}


@router.get("/api/admin/settings", response_model=SettingsOut)
def read_settings(_principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return get_settings_view(db)


@router.put("/api/admin/settings", response_model=SettingsOut)
def write_settings(
    body: SettingsUpdate,
    principal: Principal = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    return update_settings(db, body, principal.user.id)
