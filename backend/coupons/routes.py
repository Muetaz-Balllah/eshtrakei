from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend._core.deps import Principal, require_company_manager
from backend.coupons.schemas import CouponCreate, CouponOut
from backend.coupons.services import create_coupon, delete_coupon, list_coupons
from backend.db import get_db
from backend.errors import AppError

router = APIRouter(tags=["coupons"])


@router.get("/api/company/coupons", response_model=list[CouponOut])
def company_coupons(principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return list_coupons(db, principal.company_id)


@router.post("/api/company/coupons", response_model=CouponOut)
def add_coupon(body: CouponCreate, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return create_coupon(db, principal.company_id, body)


@router.delete("/api/company/coupons/{coupon_id}")
def remove_coupon(coupon_id: int, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    delete_coupon(db, principal.company_id, coupon_id)
    return {"code": "deleted", "message": "تم حذف الكوبون"}
