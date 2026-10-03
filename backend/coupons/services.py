from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.coupons.models import Coupon, CouponRedemption
from backend.coupons.schemas import CouponCreate, CouponOut
from backend.errors import AppError
from datetime import UTC

from backend.utils import quantize_money, utc_now


def _aware(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _out(row: Coupon, uses: int) -> CouponOut:
    return CouponOut(
        id=row.id,
        code=row.code,
        discount_amount=row.discount_amount,
        expires_at=row.expires_at,
        currency=get_settings().payment_currency,
        max_uses=row.max_uses,
        max_total_uses=row.max_total_uses if row.max_total_uses is not None else row.max_uses,
        redemption_count=uses,
    )


def _uses(db: Session, coupon_id: int) -> int:
    return int(db.scalar(select(func.count()).select_from(CouponRedemption).where(CouponRedemption.coupon_id == coupon_id)) or 0)


def list_coupons(db: Session, company_id: int) -> list[CouponOut]:
    rows = db.scalars(select(Coupon).where(Coupon.company_id == company_id).order_by(Coupon.created_at.desc()))
    return [_out(row, _uses(db, row.id)) for row in rows]


def delete_coupon(db: Session, company_id: int, coupon_id: int) -> None:
    from backend.payments.models import Payment

    row = db.get(Coupon, coupon_id)
    if row is None or row.company_id != company_id:
        raise AppError(404, "not_found", "الكوبون غير موجود")
    for redemption in db.scalars(select(CouponRedemption).where(CouponRedemption.coupon_id == row.id)).all():
        db.delete(redemption)
    for payment in db.scalars(select(Payment).where(Payment.coupon_id == row.id)).all():
        payment.coupon_id = None
    db.delete(row)
    db.commit()


def create_coupon(db: Session, company_id: int, body: CouponCreate) -> CouponOut:
    code = body.code.strip().upper()
    existing = db.scalar(select(Coupon).where(Coupon.company_id == company_id, Coupon.code == code))
    if existing is not None:
        raise AppError(409, "coupon_exists", "هذا الكوبون موجود مسبقاً لدى شركتك")
    if _aware(body.expires_at) <= utc_now():
        raise AppError(400, "coupon_expired", "تاريخ انتهاء الكوبون يجب أن يكون في المستقبل")
    row = Coupon(
        company_id=company_id,
        code=code,
        discount_amount=quantize_money(body.discount_amount),
        expires_at=_aware(body.expires_at),
        max_total_uses=body.max_total_uses if body.max_total_uses is not None else body.max_uses,
        max_uses=body.max_total_uses if body.max_total_uses is not None else body.max_uses,
        created_at=utc_now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _out(row, 0)


def delete_coupon(db: Session, company_id: int, coupon_id: int) -> None:
    from backend.payments.models import Payment

    row = db.get(Coupon, coupon_id)
    if row is None or row.company_id != company_id:
        raise AppError(404, "not_found", "الكوبون غير موجود")
    for redemption in db.scalars(select(CouponRedemption).where(CouponRedemption.coupon_id == row.id)).all():
        db.delete(redemption)
    for payment in db.scalars(select(Payment).where(Payment.coupon_id == row.id)).all():
        payment.coupon_id = None
    db.delete(row)
    db.commit()
