from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.advertisements.models import Advertisement
from backend.advertisements.schemas import AdvertisementPublic
from backend.companies.models import Company
from backend.companies.services import logo_url, save_image
from backend.enums import CompanyStatus
from backend.errors import AppError
from backend.utils import utc_now


def _public(row: Advertisement, company: Company) -> AdvertisementPublic:
    return AdvertisementPublic(
        id=row.id,
        company_id=company.id,
        company_name=company.name,
        title=row.title,
        body=row.body,
        image_url=logo_url(row.image_path),
    )


def list_home_ads(db: Session) -> list[AdvertisementPublic]:
    rows = db.execute(
        select(Advertisement, Company)
        .join(Company, Company.id == Advertisement.company_id)
        .where(Company.status == CompanyStatus.approved)
        .order_by(Advertisement.created_at.desc())
    )
    return [_public(ad, company) for ad, company in rows]


def list_company_ads(db: Session, company_id: int) -> list[AdvertisementPublic]:
    company = db.get(Company, company_id)
    if company is None:
        raise AppError(404, "not_found", "الشركة غير موجودة")
    rows = db.scalars(
        select(Advertisement).where(Advertisement.company_id == company_id).order_by(Advertisement.created_at.desc())
    )
    return [_public(row, company) for row in rows]


async def create_ad(
    db: Session, company_id: int, title: str, body: str, image: UploadFile | None
) -> AdvertisementPublic:
    company = db.get(Company, company_id)
    if company is None or company.status != CompanyStatus.approved:
        raise AppError(403, "company_stopped", "تم إيقاف هذه الشركة")
    if not title.strip():
        raise AppError(400, "invalid_request", "عنوان الإعلان مطلوب")
    image_path = await save_image(image, "ads")
    row = Advertisement(
        company_id=company_id,
        title=title.strip(),
        body=body.strip(),
        image_path=image_path,
        created_at=utc_now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _public(row, company)
