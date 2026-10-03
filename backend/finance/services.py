from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.companies.models import Company
from backend.errors import AppError
from backend.finance.models import FinancialEntry
from backend.utils import quantize_money, utc_now


def record(db: Session, *, company_id: int | None, banner_id: int | None, party: str, kind: str, amount: Decimal, note: str) -> None:
    db.add(
        FinancialEntry(
            company_id=company_id,
            banner_id=banner_id,
            party=party,
            kind=kind,
            amount=quantize_money(amount),
            note=note[:200],
            created_at=utc_now(),
        )
    )


def top_up_company(db: Session, company_id: int, user_id: int, amount: Decimal, simulated_outcome: str | None) -> Decimal:
    from backend.config import get_settings
    from backend.payments.schemas import PaymentRequest
    from backend.payments.services import get_payment_provider

    provider = get_payment_provider()
    if provider.name == "mock" and simulated_outcome not in {"success", "failure"}:
        raise AppError(400, "invalid_outcome", "يجب تحديد نتيجة الدفع التجريبية")
    result = provider.charge(
        PaymentRequest(
            amount=quantize_money(amount),
            currency=get_settings().payment_currency,
            idempotency_key=f"company-topup-{company_id}-{utc_now().timestamp()}",
            client_id=user_id,
            company_id=company_id,
            description="company balance top-up",
            simulated_outcome=simulated_outcome if provider.name == "mock" else None,
        )
    )
    if result.status != "succeeded":
        raise AppError(402, "payment_failed", "فشلت تعبئة الرصيد")
    return credit_company(db, company_id, amount, "شحن رصيد الشركة")


def credit_company(db: Session, company_id: int, amount: Decimal, note: str) -> Decimal:
    company = db.get(Company, company_id)
    if company is None:
        raise AppError(404, "not_found", "الشركة غير موجودة")
    value = quantize_money(amount)
    if value <= 0:
        raise AppError(400, "invalid_amount", "المبلغ يجب أن يكون أكبر من صفر")
    company.balance = quantize_money(Decimal(company.balance or 0) + value)
    record(db, company_id=company.id, banner_id=None, party="company", kind="balance_credit", amount=value, note=note or "إضافة رصيد للشركة")
    record(db, company_id=company.id, banner_id=None, party="platform", kind="balance_credit", amount=value, note=note or "إضافة رصيد للشركة")
    db.commit()
    db.refresh(company)
    return quantize_money(company.balance)


def list_entries(db: Session, company_id: int | None = None, party: str | None = None) -> list[dict]:
    query = select(FinancialEntry).order_by(FinancialEntry.created_at.desc())
    if company_id is not None:
        query = query.where(FinancialEntry.company_id == company_id)
    if party is not None:
        query = query.where(FinancialEntry.party == party)
    rows = db.scalars(query).all()
    result = []
    for row in rows:
        company = db.get(Company, row.company_id) if row.company_id else None
        result.append(
            {
                "id": row.id,
                "company_id": row.company_id,
                "company_name": company.name if company else "",
                "banner_id": row.banner_id,
                "party": row.party,
                "kind": row.kind,
                "amount": quantize_money(row.amount),
                "note": row.note,
                "created_at": row.created_at.isoformat(),
            }
        )
    return result
