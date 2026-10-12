from datetime import UTC, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.auth.models import User
from backend.companies.models import Company
from backend.config import get_settings
from backend.coupons.models import Coupon, CouponRedemption
from backend.enums import CompanyStatus, DurationUnit, PaymentStatus, SubscriptionStatus
from backend.errors import AppError
from backend.invoices.models import Invoice
from backend.packages.models import Package
from backend.payments.models import Payment
from backend.payments.schemas import PaymentRequest
from backend.payments.services import get_payment_provider
from backend.subscriptions.models import Subscription
from backend.subscriptions.schemas import ClientSubscriptions, InvoiceOut, PurchaseBody, PurchaseResult, RenewBody, SubscriptionOut
from backend.utils import add_months, libya_today, quantize_money, utc_now


def _today():
    return libya_today()


def _duration_text(amount: int, unit: DurationUnit) -> str:
    return f"{amount} {unit.value}"


def _end_date(start, amount: int, unit: DurationUnit):
    if unit == DurationUnit.days:
        return start + timedelta(days=amount)
    return add_months(start, amount)


def _sync_status(row: Subscription) -> None:
    today = _today()
    row.status = SubscriptionStatus.expired if today > row.end_date else SubscriptionStatus.active


def _speeds(text: str) -> tuple[int, int]:
    parts = text.split("/")
    download = _leading_number(parts[0]) if parts else 0
    upload = _leading_number(parts[1]) if len(parts) > 1 else download
    return download, upload


def _leading_number(text: str) -> int:
    digits = []
    for char in text:
        if char.isdigit():
            digits.append(char)
        elif digits:
            break
    return int("".join(digits)) if digits else 0


def _to_out(db: Session, row: Subscription) -> SubscriptionOut:
    _sync_status(row)
    company = db.get(Company, row.company_id)
    today = _today()
    remaining = max(0, (row.end_date - today).days) if row.start_date <= today else max(0, (row.end_date - row.start_date).days)
    display = "upcoming" if row.start_date > today else row.status.value
    return SubscriptionOut(
        id=row.id,
        company_id=row.company_id,
        company_name=company.name if company else "",
        package_name=row.package_name_snapshot,
        start_date=row.start_date,
        end_date=row.end_date,
        status=display,
        days_remaining=remaining,
        price=row.price_snapshot,
        currency=get_settings().payment_currency,
        duration=row.duration_snapshot,
        data_allowance=row.data_allowance_snapshot,
        speed=row.speed_snapshot,
        data_gb=_leading_number(row.data_allowance_snapshot),
        speed_mbps=_speeds(row.speed_snapshot)[0],
        upload_mbps=_speeds(row.speed_snapshot)[1],
    )


def _invoice_out(row: Invoice) -> InvoiceOut:
    return InvoiceOut(
        id=row.id,
        invoice_number=row.invoice_number,
        amount_paid=row.amount_paid,
        currency=row.currency,
        package_name=row.package_name_snapshot,
    )


def list_client_subscriptions(db: Session, client_id: int) -> list[SubscriptionOut]:
    rows = db.scalars(select(Subscription).where(Subscription.client_id == client_id).order_by(Subscription.created_at.desc()))
    result = [_to_out(db, row) for row in rows]
    db.commit()
    return result


def list_company_clients(db: Session, company_id: int) -> list[ClientSubscriptions]:
    rows = db.scalars(select(Subscription).where(Subscription.company_id == company_id).order_by(Subscription.created_at.desc()))
    grouped: dict[int, list[Subscription]] = {}
    for row in rows:
        grouped.setdefault(row.client_id, []).append(row)
    result = []
    for client_id, subs in grouped.items():
        user = db.get(User, client_id)
        if user is None:
            continue
        result.append(
            ClientSubscriptions(
                client_id=user.id,
                full_name=user.full_name,
                email=user.email,
                subscriptions=[_to_out(db, row) for row in subs],
            )
        )
    db.commit()
    return result


def _open_subscription(db: Session, client_id: int, company_id: int) -> Subscription | None:
    today = _today()
    return db.scalar(
        select(Subscription).where(
            Subscription.client_id == client_id,
            Subscription.company_id == company_id,
            Subscription.end_date >= today,
        )
    )


def _apply_coupon(db: Session, client_id: int, company_id: int, code: str | None, price: Decimal) -> tuple[Coupon | None, Decimal]:
    full_price = quantize_money(Decimal(price))
    if not code or not code.strip():
        return None, full_price
    coupon = db.scalar(select(Coupon).where(Coupon.company_id == company_id, Coupon.code == code.strip().upper()))
    if coupon is None:
        raise AppError(400, "invalid_coupon", "الكوبون غير صالح لهذه الشركة")
    expires_at = coupon.expires_at if coupon.expires_at.tzinfo else coupon.expires_at.replace(tzinfo=UTC)
    if expires_at <= utc_now():
        raise AppError(400, "coupon_expired", "انتهت صلاحية الكوبون")
    used = db.scalar(
        select(CouponRedemption).where(CouponRedemption.coupon_id == coupon.id, CouponRedemption.client_id == client_id)
    )
    if used is not None:
        raise AppError(400, "coupon_used", "استخدمت هذا الكوبون من قبل")
    limit = coupon.max_total_uses if coupon.max_total_uses is not None else coupon.max_uses
    if limit is not None:
        total_uses = int(db.scalar(select(func.count()).select_from(CouponRedemption).where(CouponRedemption.coupon_id == coupon.id)) or 0)
        if total_uses >= limit:
            raise AppError(400, "coupon_exhausted", "استُنفد عدد استخدامات الكوبون")
    discount = min(quantize_money(Decimal(coupon.discount_amount)), full_price)
    return coupon, quantize_money(full_price - discount)


def _next_invoice_number(db: Session) -> int:
    current = db.scalar(select(func.max(Invoice.invoice_number)))
    return int(current or 0) + 1


def _existing_payment(db: Session, key: str) -> PurchaseResult | None:
    payment = db.scalar(select(Payment).where(Payment.idempotency_key == key))
    if payment is None:
        return None
    if payment.status != PaymentStatus.succeeded or payment.subscription_id is None:
        return PurchaseResult(payment_status="failed", message="فشلت عملية الدفع")
    subscription = db.get(Subscription, payment.subscription_id)
    invoice = db.scalar(select(Invoice).where(Invoice.payment_id == payment.id))
    return PurchaseResult(
        payment_status="succeeded",
        subscription=_to_out(db, subscription) if subscription else None,
        invoice=_invoice_out(invoice) if invoice else None,
        message="تم الشراء مسبقاً",
    )


def _charge(
    db: Session,
    *,
    client: User,
    company: Company,
    package: Package,
    amount: Decimal,
    coupon: Coupon | None,
    idempotency_key: str,
    simulated_outcome: str | None,
    start,
    pay_with_wallet: bool = False,
) -> PurchaseResult:
    if pay_with_wallet:
        if amount > 0:
            from backend.wallets.services import debit

            debit(db, client.id, amount, note=package.name)
        simulated_outcome = "success"
    provider = get_payment_provider()
    if not pay_with_wallet and provider.name == "mock" and simulated_outcome not in {"success", "failure"}:
        raise AppError(400, "invalid_outcome", "يجب تحديد نتيجة الدفع التجريبية")
    if not pay_with_wallet and provider.name != "mock" and simulated_outcome is not None:
        raise AppError(400, "invalid_outcome", "لا يمكن محاكاة الدفع مع مزود حقيقي")
    currency = get_settings().payment_currency
    payment = Payment(
        client_id=client.id,
        company_id=company.id,
        package_id=package.id,
        coupon_id=coupon.id if coupon else None,
        amount=amount,
        currency=currency,
        provider="wallet" if pay_with_wallet else provider.name,
        status=PaymentStatus.failed,
        provider_reference="",
        idempotency_key=idempotency_key,
        created_at=utc_now(),
    )
    db.add(payment)
    db.flush()
    if pay_with_wallet:
        from backend.payments.schemas import PaymentResult

        result = PaymentResult(status="succeeded", provider_reference="wallet")
    else:
        result = provider.charge(
            PaymentRequest(
                amount=amount,
                currency=currency,
                idempotency_key=idempotency_key,
                client_id=client.id,
                company_id=company.id,
                description=package.name,
                simulated_outcome=simulated_outcome if provider.name == "mock" else None,
            )
        )
    payment.provider_reference = result.provider_reference
    payment.failure_code = result.failure_code
    if result.status != "succeeded":
        payment.status = PaymentStatus.failed
        db.commit()
        return PurchaseResult(payment_status="failed", message="فشلت عملية الدفع")
    end = _end_date(start, package.duration_amount, package.duration_unit)
    duration = _duration_text(package.duration_amount, package.duration_unit)
    data_text = f"{package.data_gb} GB"
    speed_text = f"{package.speed_mbps}/{package.upload_mbps or package.speed_mbps} Mbps"
    subscription = Subscription(
        client_id=client.id,
        company_id=company.id,
        package_id=package.id,
        start_date=start,
        end_date=end,
        status=SubscriptionStatus.active if start <= _today() else SubscriptionStatus.active,
        package_name_snapshot=package.name,
        price_snapshot=package.price,
        duration_snapshot=duration,
        data_allowance_snapshot=data_text,
        speed_snapshot=speed_text,
        created_at=utc_now(),
    )
    db.add(subscription)
    db.flush()
    payment.status = PaymentStatus.succeeded
    payment.subscription_id = subscription.id
    if coupon is not None:
        db.add(CouponRedemption(coupon_id=coupon.id, client_id=client.id, created_at=utc_now()))
    invoice = Invoice(
        invoice_number=_next_invoice_number(db),
        payment_id=payment.id,
        subscription_id=subscription.id,
        client_id=client.id,
        company_id=company.id,
        company_name_snapshot=company.name,
        client_name_snapshot=client.full_name,
        client_email_snapshot=client.email,
        package_name_snapshot=package.name,
        duration_snapshot=duration,
        data_allowance_snapshot=data_text,
        speed_snapshot=speed_text,
        amount_paid=amount,
        currency=currency,
        issued_at=utc_now(),
    )
    db.add(invoice)
    from backend.notifications.services import push, push_company_manager

    push(db, client.id, f"purchase_{subscription.id}", f"تم تأكيد شراء باقة {package.name}", subscription.id)
    push_company_manager(db, company.id, f"sale_{subscription.id}", f"اشتراك جديد من {client.full_name}: {package.name}")
    db.commit()
    db.refresh(subscription)
    db.refresh(invoice)
    from backend.invoices.services import deliver_invoice

    deliver_invoice(db, invoice)
    db.refresh(invoice)
    return PurchaseResult(
        payment_status="succeeded",
        subscription=_to_out(db, subscription),
        invoice=_invoice_out(invoice),
        message="تم الشراء بنجاح. غطى الكوبون قيمة الاشتراك ولم يُخصم من المحفظة" if coupon is not None and amount == 0 else "تم الشراء بنجاح",
    )


def purchase(db: Session, client_id: int, body: PurchaseBody) -> PurchaseResult:
    existing = _existing_payment(db, body.idempotency_key)
    if existing is not None:
        return existing
    client = db.get(User, client_id)
    company = db.get(Company, body.company_id)
    package = db.get(Package, body.package_id)
    if client is None or company is None or company.status != CompanyStatus.approved:
        raise AppError(404, "not_found", "الشركة غير متاحة")
    if package is None or package.company_id != company.id or not package.is_available:
        raise AppError(404, "not_found", "الباقة غير متاحة")
    if _open_subscription(db, client.id, company.id) is not None:
        raise AppError(409, "active_subscription", "لديك اشتراك قائم مع هذه الشركة. يمكنك تجديده فقط")
    coupon, amount = _apply_coupon(db, client.id, company.id, body.coupon_code, package.price)
    return _charge(
        db,
        client=client,
        company=company,
        package=package,
        amount=amount,
        coupon=coupon,
        idempotency_key=body.idempotency_key,
        simulated_outcome=body.simulated_outcome,
        start=_today(),
        pay_with_wallet=body.pay_with_wallet,
    )


def renew(db: Session, client_id: int, subscription_id: int, body: RenewBody, company_id: int | None = None) -> PurchaseResult:
    existing = _existing_payment(db, body.idempotency_key)
    if existing is not None:
        return existing
    current = db.get(Subscription, subscription_id)
    if current is None or (company_id is None and current.client_id != client_id):
        raise AppError(404, "not_found", "الاشتراك غير موجود")
    if company_id is not None and current.company_id != company_id:
        raise AppError(404, "not_found", "الاشتراك غير موجود")
    later = db.scalar(
        select(Subscription.id).where(
            Subscription.client_id == current.client_id,
            Subscription.company_id == current.company_id,
            Subscription.start_date > current.end_date,
        )
    )
    if later is not None:
        raise AppError(409, "already_renewed", "تم تجديد هذا الاشتراك مسبقاً")
    client = db.get(User, current.client_id)
    company = db.get(Company, current.company_id)
    package = db.get(Package, current.package_id)
    if client is None or company is None or company.status != CompanyStatus.approved or package is None:
        raise AppError(404, "not_found", "لا يمكن تجديد هذا الاشتراك")
    start = current.end_date + timedelta(days=1) if current.end_date >= _today() else _today()
    return _charge(
        db,
        client=client,
        company=company,
        package=package,
        amount=package.price,
        coupon=None,
        idempotency_key=body.idempotency_key,
        simulated_outcome=body.simulated_outcome,
        start=start,
        pay_with_wallet=body.pay_with_wallet,
    )
