from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend._core.deps import Principal, require_client, require_company_manager, require_platform_admin
from backend.companies.schemas import CompanyAdmin, CompanyPublic, CompanyUpdate, CreateManagerRequest, JoinRequestPublic, ManagerCompany
from backend.companies.services import (
    approve_request,
    create_manager,
    get_manager_company,
    update_manager_company,
    list_available,
    list_for_admin,
    list_join_requests,
    reject_request,
    resume_company,
    stop_company,
    submit_join_request,
)
from backend.db import get_db

router = APIRouter(tags=["companies"])


@router.get("/api/companies", response_model=list[CompanyPublic])
def companies_for_client(_principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    return list_available(db)


@router.get("/api/company/me", response_model=ManagerCompany)
def my_company(principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    return get_manager_company(db, principal.company_id)


class TopUpBody(BaseModel):
    amount: Decimal = Field(gt=0)
    simulated_outcome: str | None = "success"


@router.post("/api/company/balance/topups")
def top_up_balance(body: TopUpBody, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    from backend.errors import AppError
    from backend.finance.services import top_up_company

    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    balance = top_up_company(db, principal.company_id, principal.user.id, body.amount, body.simulated_outcome)
    return {"balance": balance, "message": "تم شحن رصيد الشركة"}


@router.put("/api/company/me", response_model=ManagerCompany)
def edit_company(body: CompanyUpdate, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    return update_manager_company(db, principal.company_id, body.name, body.description, body.phone)


@router.post("/api/join-requests", response_model=JoinRequestPublic)
async def create_join_request(
    name: str = Form(),
    description: str = Form(""),
    phone: str = Form(),
    logo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    from backend.errors import AppError

    if not name.strip() or not phone.strip():
        raise AppError(400, "invalid_request", "اسم الشركة ورقم الهاتف مطلوبان")
    return await submit_join_request(db, name, description, phone, logo)


@router.get("/api/admin/companies", response_model=list[CompanyAdmin])
def admin_companies(_principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return list_for_admin(db)


@router.get("/api/admin/join-requests", response_model=list[JoinRequestPublic])
def admin_requests(_principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return list_join_requests(db)


@router.post("/api/admin/join-requests/{request_id}/approve", response_model=CompanyAdmin)
def approve(request_id: int, principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return approve_request(db, request_id, principal.user.id)


@router.post("/api/admin/join-requests/{request_id}/reject", response_model=JoinRequestPublic)
def reject(request_id: int, principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return reject_request(db, request_id, principal.user.id)


@router.post("/api/admin/companies/{company_id}/manager")
def add_manager(
    company_id: int,
    body: CreateManagerRequest,
    _principal: Principal = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    create_manager(db, company_id, body.full_name, body.email, body.password)
    return {"code": "manager_created", "message": "تم إنشاء حساب موظف الشركة"}


@router.post("/api/admin/companies/{company_id}/stop", response_model=CompanyAdmin)
def stop(company_id: int, _principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return stop_company(db, company_id)


@router.post("/api/admin/companies/{company_id}/resume", response_model=CompanyAdmin)
def resume(company_id: int, _principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return resume_company(db, company_id)
