from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.models import User
from backend.companies.models import Company
from backend.complaints.models import Complaint
from backend.complaints.schemas import ComplaintCreate, ComplaintOut, ReplyBody
from backend.errors import AppError
from backend.utils import utc_now


def _out(db: Session, row: Complaint) -> ComplaintOut:
    company = db.get(Company, row.company_id) if row.company_id else None
    client = db.get(User, row.client_id)
    return ComplaintOut(
        id=row.id,
        kind=row.kind,
        target=row.target,
        company_id=row.company_id,
        company_name=company.name if company else None,
        client_name=client.full_name if client else "",
        client_phone=client.phone if client else None,
        message=row.message,
        created_at=row.created_at,
        reply_message=row.reply_message,
        replied_at=row.replied_at,
    )


def create_complaint(db: Session, client_id: int, body: ComplaintCreate) -> ComplaintOut:
    company_id = None
    if body.target == "company":
        if body.company_id is None or db.get(Company, body.company_id) is None:
            raise AppError(404, "not_found", "الشركة غير موجودة")
        company_id = body.company_id
    row = Complaint(
        client_id=client_id,
        kind=body.kind,
        target=body.target,
        company_id=company_id,
        message=body.message.strip(),
        created_at=utc_now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _out(db, row)


def list_for_client(db: Session, client_id: int) -> list[ComplaintOut]:
    rows = db.scalars(select(Complaint).where(Complaint.client_id == client_id).order_by(Complaint.created_at.desc()))
    return [_out(db, row) for row in rows]


def list_for_company(db: Session, company_id: int) -> list[ComplaintOut]:
    rows = db.scalars(
        select(Complaint).where(Complaint.target == "company", Complaint.company_id == company_id).order_by(Complaint.created_at.desc())
    )
    return [_out(db, row) for row in rows]


def create_support(db: Session, manager_id: int, company_id: int, message: str) -> ComplaintOut:
    row = Complaint(
        client_id=manager_id,
        kind="technical_support",
        target="platform",
        company_id=company_id,
        message=message.strip(),
        created_at=utc_now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _out(db, row)


def list_support(db: Session, company_id: int) -> list[ComplaintOut]:
    rows = db.scalars(
        select(Complaint)
        .where(Complaint.target == "platform", Complaint.company_id == company_id)
        .order_by(Complaint.created_at.desc())
    )
    return [_out(db, row) for row in rows]


def list_for_platform(db: Session) -> list[ComplaintOut]:
    rows = db.scalars(select(Complaint).where(Complaint.target == "platform").order_by(Complaint.created_at.desc()))
    return [_out(db, row) for row in rows]


def reply(db: Session, complaint_id: int, user_id: int, body: ReplyBody, company_id: int | None) -> ComplaintOut:
    row = db.get(Complaint, complaint_id)
    if row is None:
        raise AppError(404, "not_found", "الشكوى غير موجودة")
    if company_id is not None and (row.target != "company" or row.company_id != company_id):
        raise AppError(404, "not_found", "الشكوى غير موجودة")
    if company_id is None and row.target != "platform":
        raise AppError(404, "not_found", "الشكوى غير موجودة")
    row.reply_message = body.message.strip()
    row.replied_by = user_id
    row.replied_at = utc_now()
    db.commit()
    db.refresh(row)
    return _out(db, row)
