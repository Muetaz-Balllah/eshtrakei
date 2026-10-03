from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend._core.deps import Principal, require_client, require_company_manager, require_platform_admin
from backend.companies.models import Company
from backend.complaints.schemas import ComplaintCreate, ComplaintOut, ReplyBody
from backend.complaints.services import create_complaint, create_support, list_for_client, list_for_company, list_for_platform, list_support, reply
from backend.db import get_db
from backend.errors import AppError

router = APIRouter(tags=["complaints"])


@router.get("/api/complaints/companies")
def complaint_companies(_principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    rows = db.scalars(select(Company).order_by(Company.name))
    return [{"id": row.id, "name": row.name} for row in rows]


@router.post("/api/complaints", response_model=ComplaintOut)
def submit(body: ComplaintCreate, principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    return create_complaint(db, principal.user.id, body)


@router.get("/api/complaints", response_model=list[ComplaintOut])
def mine(principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    return list_for_client(db, principal.user.id)


@router.get("/api/company/complaints", response_model=list[ComplaintOut])
def company_complaints(principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return list_for_company(db, principal.company_id)


@router.post("/api/company/complaints/{complaint_id}/reply", response_model=ComplaintOut)
def company_reply(
    complaint_id: int,
    body: ReplyBody,
    principal: Principal = Depends(require_company_manager),
    db: Session = Depends(get_db),
):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return reply(db, complaint_id, principal.user.id, body, principal.company_id)


@router.get("/api/company/support", response_model=list[ComplaintOut])
def company_support(principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return list_support(db, principal.company_id)


@router.post("/api/company/support", response_model=ComplaintOut)
def send_support(body: ReplyBody, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return create_support(db, principal.user.id, principal.company_id, body.message)


@router.get("/api/admin/complaints", response_model=list[ComplaintOut])
def platform_complaints(_principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return list_for_platform(db)


@router.post("/api/admin/complaints/{complaint_id}/reply", response_model=ComplaintOut)
def platform_reply(
    complaint_id: int,
    body: ReplyBody,
    principal: Principal = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    return reply(db, complaint_id, principal.user.id, body, None)
