from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend._core.deps import Principal, require_client, require_company_manager
from backend.advertisements.schemas import AdvertisementPublic
from backend.advertisements.services import create_ad, list_company_ads, list_home_ads
from backend.db import get_db
from backend.errors import AppError

router = APIRouter(tags=["advertisements"])


@router.get("/api/advertisements", response_model=list[AdvertisementPublic])
def home_ads(_principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    return list_home_ads(db)


@router.get("/api/company/advertisements", response_model=list[AdvertisementPublic])
def company_ads(principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return list_company_ads(db, principal.company_id)


@router.post("/api/company/advertisements", response_model=AdvertisementPublic)
async def add_ad(
    title: str = Form(),
    body: str = Form(""),
    image: UploadFile | None = File(None),
    principal: Principal = Depends(require_company_manager),
    db: Session = Depends(get_db),
):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return await create_ad(db, principal.company_id, title, body, image)
