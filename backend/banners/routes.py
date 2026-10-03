from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend._core.deps import Principal, require_client, require_company_manager, require_platform_admin
from backend.banners.schemas import BannerOut, LedgerOut
from backend.banners.services import approve_banner, list_for_admin, list_for_company, list_published, reject_banner, remove_banner, submit_banner
from backend.db import get_db
from backend.finance.services import credit_company, list_entries
from backend.settings.services import banner_price

router = APIRouter(tags=["banners"])


class CreditBody(BaseModel):
    amount: Decimal = Field(gt=0)
    note: str = ""


@router.get("/api/banners", response_model=list[BannerOut])
def client_banners(_principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    return list_published(db)


@router.get("/api/company/banner-price")
def company_banner_price(_principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    return {"price": banner_price(db)}


@router.get("/api/company/banners", response_model=list[BannerOut])
def company_banners(principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    return list_for_company(db, principal.company_id or 0)


@router.post("/api/company/banners", response_model=BannerOut)
async def add_company_banner(
    title: str = Form(),
    body: str = Form(""),
    image: UploadFile | None = File(None),
    principal: Principal = Depends(require_company_manager),
    db: Session = Depends(get_db),
):
    if principal.company_id is None:
        from backend.errors import AppError

        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return await submit_banner(db, principal.company_id, title, body, image)


@router.get("/api/company/ledger", response_model=list[LedgerOut])
def company_ledger(principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    return list_entries(db, company_id=principal.company_id, party="company")


@router.get("/api/admin/banners", response_model=list[BannerOut])
def admin_banners(_principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return list_for_admin(db)


@router.post("/api/admin/banners/{banner_id}/approve", response_model=BannerOut)
def approve(banner_id: int, principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return approve_banner(db, banner_id, principal.user.id)


@router.post("/api/admin/banners/{banner_id}/reject", response_model=BannerOut)
def reject(banner_id: int, principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return reject_banner(db, banner_id, principal.user.id)


@router.delete("/api/admin/banners/{banner_id}")
def delete_banner(banner_id: int, _principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    remove_banner(db, banner_id)
    return {"code": "deleted", "message": "تم إيقاف البانر"}


@router.get("/api/admin/ledger", response_model=list[LedgerOut])
def admin_ledger(_principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return list_entries(db, party="platform")


@router.post("/api/admin/companies/{company_id}/credits")
def credit(company_id: int, body: CreditBody, _principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    balance = credit_company(db, company_id, body.amount, body.note)
    return {"balance": balance, "message": "تمت إضافة الرصيد"}
