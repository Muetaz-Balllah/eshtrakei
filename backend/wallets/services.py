from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.errors import AppError
from backend.payments.schemas import PaymentRequest
from backend.payments.services import get_payment_provider
from backend.utils import quantize_money, utc_now
from backend.wallets.models import Wallet, WalletTransaction
from backend.wallets.schemas import WalletOut, WalletTxOut


def get_or_create(db: Session, user_id: int) -> Wallet:
    wallet = db.get(Wallet, user_id)
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance=Decimal("0.00"))
        db.add(wallet)
        db.flush()
    return wallet


def view(db: Session, user_id: int) -> WalletOut:
    wallet = get_or_create(db, user_id)
    rows = db.scalars(
        select(WalletTransaction).where(WalletTransaction.user_id == user_id).order_by(WalletTransaction.created_at.desc())
    ).all()
    db.commit()
    return WalletOut(
        balance=quantize_money(wallet.balance),
        currency=get_settings().payment_currency,
        transactions=[
            WalletTxOut(id=row.id, amount=row.amount, kind=row.kind, note=row.note or "", created_at=row.created_at) for row in rows
        ],
    )


def top_up(db: Session, user_id: int, amount: Decimal, simulated_outcome: str | None) -> WalletOut:
    provider = get_payment_provider()
    if provider.name == "mock" and simulated_outcome not in {"success", "failure"}:
        raise AppError(400, "invalid_outcome", "يجب تحديد نتيجة الدفع التجريبية")
    result = provider.charge(
        PaymentRequest(
            amount=amount,
            currency=get_settings().payment_currency,
            idempotency_key=f"wallet-{user_id}-{utc_now().timestamp()}",
            client_id=user_id,
            company_id=0,
            description="wallet top-up",
            simulated_outcome=simulated_outcome if provider.name == "mock" else None,
        )
    )
    if result.status != "succeeded":
        raise AppError(402, "payment_failed", "فشلت تعبئة الرصيد")
    wallet = get_or_create(db, user_id)
    wallet.balance = quantize_money(Decimal(wallet.balance) + amount)
    db.add(WalletTransaction(user_id=user_id, amount=quantize_money(amount), kind="topup", note="شحن رصيد المحفظة", created_at=utc_now()))
    db.commit()
    return view(db, user_id)


def debit(db: Session, user_id: int, amount: Decimal, note: str = "") -> None:
    wallet = get_or_create(db, user_id)
    if Decimal(wallet.balance) < amount:
        raise AppError(402, "insufficient_balance", "رصيد المحفظة غير كافٍ")
    wallet.balance = quantize_money(Decimal(wallet.balance) - amount)
    db.add(
        WalletTransaction(
            user_id=user_id,
            amount=quantize_money(amount),
            kind="purchase",
            note=note or "دفع من المحفظة",
            created_at=utc_now(),
        )
    )
