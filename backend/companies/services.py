from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend._core.security import hash_password
from backend.auth.models import User
from backend.companies.models import Company, CompanyJoinRequest, CompanyManager
from backend.companies.schemas import CompanyAdmin, CompanyPublic, JoinRequestPublic, ManagerCompany
from backend.utils import quantize_money
from backend.enums import CompanyStatus, JoinRequestStatus, UserRole
from backend.errors import AppError
from backend.utils import utc_now

STORAGE = Path("backend/storage")
ALLOWED_IMAGE_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


def logo_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"/api/media/{path}"


async def save_image(upload: UploadFile | None, folder: str) -> str | None:
    if upload is None or not upload.filename:
        return None
    ext = ALLOWED_IMAGE_TYPES.get(upload.content_type or "")
    if ext is None:
        raise AppError(400, "invalid_image", "صيغة الشعار يجب أن تكون PNG أو JPG أو WEBP")
    target_dir = STORAGE / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid4().hex}{ext}"
    content = await upload.read()
    if len(content) > 2_000_000:
        raise AppError(400, "image_too_large", "حجم الصورة أكبر من الحد المسموح")
    (target_dir / name).write_bytes(content)
    return f"{folder}/{name}"


def to_public(company: Company) -> CompanyPublic:
    return CompanyPublic(
        id=company.id,
        name=company.name,
        description=company.description,
        phone=company.phone,
        logo_url=logo_url(company.logo_path),
    )


def list_available(db: Session) -> list[CompanyPublic]:
    rows = db.scalars(select(Company).where(Company.status == CompanyStatus.approved).order_by(Company.name))
    return [to_public(row) for row in rows]


def list_for_admin(db: Session) -> list[CompanyAdmin]:
    rows = db.scalars(select(Company).order_by(Company.created_at.desc()))
    result = []
    for row in rows:
        manager = db.scalar(select(CompanyManager).where(CompanyManager.company_id == row.id))
        result.append(
            CompanyAdmin(
                **to_public(row).model_dump(),
                status=row.status,
                has_manager=manager is not None,
            )
        )
    return result


def _manager(company: Company) -> ManagerCompany:
    return ManagerCompany(**to_public(company).model_dump(), balance=quantize_money(Decimal(company.balance or 0)))


def update_manager_company(db: Session, company_id: int | None, name: str, description: str, phone: str) -> ManagerCompany:
    if company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    company = db.get(Company, company_id)
    if company is None or company.status == CompanyStatus.stopped:
        raise AppError(403, "company_stopped", "تم إيقاف هذه الشركة")
    company.name = name.strip()
    company.description = description.strip()
    company.phone = phone.strip()
    company.updated_at = utc_now()
    db.commit()
    db.refresh(company)
    return _manager(company)


def get_manager_company(db: Session, company_id: int | None) -> ManagerCompany:
    if company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    company = db.get(Company, company_id)
    if company is None or company.status == CompanyStatus.stopped:
        raise AppError(403, "company_stopped", "تم إيقاف هذه الشركة")
    return _manager(company)


async def submit_join_request(
    db: Session, name: str, description: str, phone: str, logo: UploadFile | None
) -> JoinRequestPublic:
    logo_path = await save_image(logo, "logos")
    row = CompanyJoinRequest(
        name=name.strip(),
        description=description.strip(),
        phone=phone.strip(),
        logo_path=logo_path,
        status=JoinRequestStatus.pending,
        created_at=utc_now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _request_public(row)


def list_join_requests(db: Session) -> list[JoinRequestPublic]:
    rows = db.scalars(select(CompanyJoinRequest).order_by(CompanyJoinRequest.created_at.desc()))
    return [_request_public(row) for row in rows]


def approve_request(db: Session, request_id: int, admin_id: int) -> CompanyAdmin:
    row = db.get(CompanyJoinRequest, request_id)
    if row is None or row.status != JoinRequestStatus.pending:
        raise AppError(404, "not_found", "طلب الانضمام غير موجود")
    now = utc_now()
    company = Company(
        name=row.name,
        description=row.description,
        phone=row.phone,
        logo_path=row.logo_path,
        status=CompanyStatus.approved,
        created_at=now,
        updated_at=now,
    )
    db.add(company)
    db.flush()
    row.status = JoinRequestStatus.approved
    row.company_id = company.id
    row.reviewed_by = admin_id
    row.reviewed_at = now
    db.commit()
    db.refresh(company)
    return CompanyAdmin(**to_public(company).model_dump(), status=company.status, has_manager=False)


def reject_request(db: Session, request_id: int, admin_id: int) -> JoinRequestPublic:
    row = db.get(CompanyJoinRequest, request_id)
    if row is None or row.status != JoinRequestStatus.pending:
        raise AppError(404, "not_found", "طلب الانضمام غير موجود")
    row.status = JoinRequestStatus.rejected
    row.reviewed_by = admin_id
    row.reviewed_at = utc_now()
    db.commit()
    db.refresh(row)
    return _request_public(row)


def create_manager(db: Session, company_id: int, full_name: str, email: str, password: str) -> None:
    company = db.get(Company, company_id)
    if company is None:
        raise AppError(404, "not_found", "الشركة غير موجودة")
    if company.status != CompanyStatus.approved:
        raise AppError(409, "company_not_approved", "يمكن إنشاء موظف فقط لشركة تمت الموافقة عليها")
    if db.scalar(select(CompanyManager).where(CompanyManager.company_id == company_id)) is not None:
        raise AppError(409, "manager_exists", "هذه الشركة لديها موظف بالفعل")
    normalized = email.lower()
    if db.scalar(select(User).where(User.email == normalized)) is not None:
        raise AppError(409, "email_taken", "هذا البريد الإلكتروني مستخدم بالفعل")
    user = User(
        full_name=full_name.strip(),
        email=normalized,
        password_hash=hash_password(password),
        role=UserRole.company_manager,
        is_active=True,
        created_at=utc_now(),
    )
    db.add(user)
    db.flush()
    db.add(CompanyManager(user_id=user.id, company_id=company.id, created_at=utc_now()))
    db.commit()


def resume_company(db: Session, company_id: int) -> CompanyAdmin:
    company = db.get(Company, company_id)
    if company is None:
        raise AppError(404, "not_found", "الشركة غير موجودة")
    if company.status != CompanyStatus.stopped:
        raise AppError(409, "company_not_stopped", "الشركة ليست موقوفة")
    company.status = CompanyStatus.approved
    company.updated_at = utc_now()
    db.commit()
    db.refresh(company)
    manager = db.scalar(select(CompanyManager).where(CompanyManager.company_id == company.id))
    return CompanyAdmin(**to_public(company).model_dump(), status=company.status, has_manager=manager is not None)


def stop_company(db: Session, company_id: int) -> CompanyAdmin:
    company = db.get(Company, company_id)
    if company is None:
        raise AppError(404, "not_found", "الشركة غير موجودة")
    company.status = CompanyStatus.stopped
    company.updated_at = utc_now()
    db.commit()
    db.refresh(company)
    manager = db.scalar(select(CompanyManager).where(CompanyManager.company_id == company.id))
    return CompanyAdmin(**to_public(company).model_dump(), status=company.status, has_manager=manager is not None)


def _request_public(row: CompanyJoinRequest) -> JoinRequestPublic:
    return JoinRequestPublic(
        id=row.id,
        name=row.name,
        description=row.description,
        phone=row.phone,
        logo_url=logo_url(row.logo_path),
        status=row.status,
        created_at=row.created_at,
    )
