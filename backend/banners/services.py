from decimal import Decimal

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.banners.models import PlatformBanner
from backend.banners.schemas import BannerOut
from backend.companies.models import Company
from backend.companies.services import logo_url, save_image
from backend.errors import AppError
from backend.finance.services import record
from backend.settings.services import banner_price
from backend.utils import quantize_money, utc_now


def _out(db: Session, row: PlatformBanner, include_balance: bool = False) -> BannerOut:
    company = db.get(Company, row.company_id) if row.company_id else None
    return BannerOut(
        id=row.id,
        title=row.title,
        body=row.body,
        image_url=logo_url(row.image_path),
        is_active=row.is_active,
        status=row.status,
        price=quantize_money(Decimal(row.price or 0)),
        company_id=row.company_id,
        company_name=company.name if company else "",
        company_balance=quantize_money(Decimal(company.balance or 0)) if include_balance and company else None,
    )


def list_published(db: Session) -> list[BannerOut]:
    rows = db.scalars(
        select(PlatformBanner)
        .where(PlatformBanner.status == "approved", PlatformBanner.is_active.is_(True))
        .order_by(PlatformBanner.id.desc())
    ).all()
    return [_out(db, row) for row in rows]


def list_for_admin(db: Session) -> list[BannerOut]:
    rows = db.scalars(select(PlatformBanner).order_by(PlatformBanner.id.desc())).all()
    return [_out(db, row, include_balance=True) for row in rows]


def list_for_company(db: Session, company_id: int) -> list[BannerOut]:
    rows = db.scalars(
        select(PlatformBanner).where(PlatformBanner.company_id == company_id).order_by(PlatformBanner.id.desc())
    ).all()
    return [_out(db, row) for row in rows]


async def submit_banner(db: Session, company_id: int, title: str, body: str, image: UploadFile | None) -> BannerOut:
    company = db.get(Company, company_id)
    if company is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    path = await save_image(image, "banners")
    row = PlatformBanner(
        company_id=company_id,
        title=title.strip(),
        body=body.strip(),
        image_path=path,
        is_active=False,
        status="pending_approval",
        price=banner_price(db),
        created_at=utc_now(),
    )
    db.add(row)
    from backend.enums import UserRole
    from backend.notifications.services import push_role

    push_role(db, UserRole.platform_admin, f"banner_request_{company_id}_{title.strip()[:20]}", f"طلب بانر جديد من {company.name}: {title.strip()}")
    db.commit()
    db.refresh(row)
    return _out(db, row)


def approve_banner(db: Session, banner_id: int, admin_id: int) -> BannerOut:
    row = db.get(PlatformBanner, banner_id)
    if row is None or row.company_id is None:
        raise AppError(404, "not_found", "البانر غير موجود")
    if row.status != "pending_approval":
        raise AppError(400, "banner_reviewed", "تمت مراجعة هذا البانر مسبقاً")
    company = db.get(Company, row.company_id)
    if company is None:
        raise AppError(404, "not_found", "الشركة غير موجودة")
    price = quantize_money(Decimal(row.price or 0))
    balance = quantize_money(Decimal(company.balance or 0))
    if balance < price:
        raise AppError(402, "insufficient_balance", "رصيد الشركة غير كافٍ لرسوم البانر")
    company.balance = quantize_money(balance - price)
    row.status = "approved"
    row.is_active = True
    row.reviewed_at = utc_now()
    row.reviewed_by = admin_id
    note = f"رسوم بانر: {row.title}"
    record(db, company_id=company.id, banner_id=row.id, party="company", kind="banner_expense", amount=price, note=note)
    record(db, company_id=company.id, banner_id=row.id, party="platform", kind="banner_income", amount=price, note=note)
    from backend.notifications.services import push_company_manager

    push_company_manager(db, company.id, f"banner_approved_{row.id}", f"تمت الموافقة على البانر {row.title} وخصم {price}")
    db.commit()
    db.refresh(row)
    return _out(db, row, include_balance=True)


def reject_banner(db: Session, banner_id: int, admin_id: int) -> BannerOut:
    row = db.get(PlatformBanner, banner_id)
    if row is None:
        raise AppError(404, "not_found", "البانر غير موجود")
    if row.status != "pending_approval":
        raise AppError(400, "banner_reviewed", "تمت مراجعة هذا البانر مسبقاً")
    row.status = "rejected"
    row.is_active = False
    row.reviewed_at = utc_now()
    row.reviewed_by = admin_id
    from backend.notifications.services import push_company_manager

    if row.company_id is not None:
        push_company_manager(db, row.company_id, f"banner_rejected_{row.id}", f"تم رفض البانر {row.title}")
    db.commit()
    db.refresh(row)
    return _out(db, row, include_balance=True)


def remove_banner(db: Session, banner_id: int) -> None:
    row = db.get(PlatformBanner, banner_id)
    if row is None:
        return
    row.is_active = False
    if row.status == "approved":
        row.status = "rejected"
    db.commit()
