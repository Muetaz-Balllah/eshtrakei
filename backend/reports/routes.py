from decimal import Decimal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend._core.deps import Principal, require_company_manager, require_platform_admin
from backend.companies.models import Company
from backend.db import get_db
from backend.errors import AppError
from backend.reports.schemas import CompanyReport, PlatformPerformance
from backend.reports.services import company_report, platform_performance
from backend.utils import quantize_money


class TargetBody(BaseModel):
    monthly_sales_target: Decimal = Field(ge=0)

router = APIRouter(tags=["reports"])


@router.get("/api/company/reports/sales", response_model=CompanyReport)
def sales(principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return company_report(db, principal.company_id)


@router.put("/api/company/sales-target", response_model=CompanyReport)
def set_target(body: TargetBody, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    company = db.get(Company, principal.company_id)
    if company is None:
        raise AppError(404, "not_found", "الشركة غير موجودة")
    company.monthly_sales_target = quantize_money(body.monthly_sales_target)
    db.commit()
    return company_report(db, principal.company_id)


@router.get("/api/admin/performance", response_model=PlatformPerformance)
def performance(_principal: Principal = Depends(require_platform_admin), db: Session = Depends(get_db)):
    return platform_performance(db)
