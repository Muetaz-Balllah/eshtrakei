from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.companies.models import Company
from backend.config import get_settings
from backend.enums import CompanyStatus, DurationUnit
from backend.errors import AppError
from backend.packages.models import Package
from backend.packages.schemas import PackageBody, PackageOut
from backend.subscriptions.models import Subscription
from backend.utils import libya_today, quantize_money, utc_now


def to_out(row: Package) -> PackageOut:
    return PackageOut(
        id=row.id,
        company_id=row.company_id,
        name=row.name,
        price=row.price,
        duration_amount=row.duration_amount,
        duration_unit=row.duration_unit,
        data_gb=row.data_gb,
        speed_mbps=row.speed_mbps,
        download_mbps=row.speed_mbps,
        upload_mbps=row.upload_mbps or row.speed_mbps,
        is_available=row.is_available,
        currency=get_settings().payment_currency,
    )


def list_for_manager(db: Session, company_id: int) -> list[PackageOut]:
    rows = db.scalars(select(Package).where(Package.company_id == company_id).order_by(Package.name)).all()
    today = libya_today()
    counts: dict[int, int] = {}
    subscriptions = db.scalars(select(Subscription).where(Subscription.company_id == company_id)).all()
    for subscription in subscriptions:
        if subscription.start_date <= today <= subscription.end_date:
            counts[subscription.package_id] = counts.get(subscription.package_id, 0) + 1
    result = []
    for row in rows:
        item = to_out(row)
        item.active_subscribers = counts.get(row.id, 0)
        result.append(item)
    return result


def list_for_client(db: Session, company_id: int) -> list[PackageOut]:
    company = db.get(Company, company_id)
    if company is None or company.status != CompanyStatus.approved:
        raise AppError(404, "not_found", "الشركة غير متاحة")
    rows = db.scalars(
        select(Package).where(Package.company_id == company_id, Package.is_available.is_(True)).order_by(Package.name)
    )
    return [to_out(row) for row in rows]


def create_package(db: Session, company_id: int, body: PackageBody) -> PackageOut:
    now = utc_now()
    row = Package(
        company_id=company_id,
        name=body.name.strip(),
        price=quantize_money(body.price),
        duration_amount=body.duration_amount,
        duration_unit=DurationUnit.days,
        data_gb=body.data_gb,
        speed_mbps=body.download_mbps or body.speed_mbps or 0,
        upload_mbps=body.upload_mbps or body.download_mbps or body.speed_mbps or 0,
        is_available=True,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return to_out(row)


def _owned(db: Session, company_id: int, package_id: int) -> Package:
    row = db.get(Package, package_id)
    if row is None or row.company_id != company_id:
        raise AppError(404, "not_found", "الباقة غير موجودة")
    return row


def update_package(db: Session, company_id: int, package_id: int, body: PackageBody) -> PackageOut:
    row = _owned(db, company_id, package_id)
    row.name = body.name.strip()
    row.price = quantize_money(body.price)
    row.duration_amount = body.duration_amount
    row.duration_unit = DurationUnit.days
    row.data_gb = body.data_gb
    row.speed_mbps = body.download_mbps or body.speed_mbps or row.speed_mbps
    row.upload_mbps = body.upload_mbps or row.speed_mbps
    row.updated_at = utc_now()
    db.commit()
    db.refresh(row)
    return to_out(row)


def resume_package(db: Session, company_id: int, package_id: int) -> PackageOut:
    row = _owned(db, company_id, package_id)
    row.is_available = True
    row.updated_at = utc_now()
    db.commit()
    db.refresh(row)
    return to_out(row)


def stop_package(db: Session, company_id: int, package_id: int) -> PackageOut:
    row = _owned(db, company_id, package_id)
    row.is_available = False
    row.updated_at = utc_now()
    db.commit()
    db.refresh(row)
    return to_out(row)


def delete_package(db: Session, company_id: int, package_id: int) -> dict:
    from backend.subscriptions.models import Subscription
    from backend.utils import utc_now as now_fn

    row = _owned(db, company_id, package_id)
    today = now_fn().date()
    active = db.scalar(
        select(Subscription.id).where(Subscription.package_id == row.id, Subscription.end_date >= today)
    )
    if active is not None:
        row.is_available = False
        row.updated_at = now_fn()
        db.commit()
        return {"hidden": True}
    db.delete(row)
    db.commit()
    return {"hidden": False}
