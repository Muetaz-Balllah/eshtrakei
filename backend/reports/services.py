from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.auth.models import User
from backend.companies.models import Company, CompanyJoinRequest
from backend.config import get_settings
from backend.enums import CompanyStatus, JoinRequestStatus, PaymentStatus, UserRole
from backend.packages.models import Package
from backend.payments.models import Payment
from backend.reports.schemas import CompanyReport, MonthPoint, PlatformPerformance, SaleRow
from backend.settings.services import commission_rate, get_settings_view
from backend.subscriptions.models import Subscription
from backend.utils import libya_today, quantize_money


def company_report(db: Session, company_id: int) -> CompanyReport:
    rate = commission_rate(db)
    currency = get_settings().payment_currency
    rows = db.execute(
        select(Payment, User, Package)
        .join(User, User.id == Payment.client_id)
        .join(Package, Package.id == Payment.package_id)
        .where(Payment.company_id == company_id, Payment.status == PaymentStatus.succeeded)
        .order_by(Payment.created_at.desc())
    ).all()
    sales = []
    total = Decimal("0")
    profit = Decimal("0")
    for payment, user, package in rows:
        amount = Decimal(payment.amount)
        total += amount
        profit += amount * (Decimal("1") - Decimal(str(rate)))
        sales.append(
            SaleRow(
                created_at=payment.created_at,
                client_name=user.full_name,
                package_name=package.name,
                amount=amount,
                currency=currency,
            )
        )
    months = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
    now = datetime.now().astimezone()

    def local(value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(now.tzinfo)

    def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
        index = year * 12 + (month - 1) + delta
        return index // 12, index % 12 + 1

    month_buckets: dict[tuple[int, int], Decimal] = {}
    week_buckets: dict[tuple[int, int], Decimal] = {}
    year_buckets: dict[int, Decimal] = {}
    month_counts: dict[tuple[int, int], int] = {}
    client_times: dict[int, list[datetime]] = {}
    for payment, user, _package in rows:
        created = local(payment.created_at)
        amount = Decimal(payment.amount)
        month_key = (created.year, created.month)
        month_buckets[month_key] = month_buckets.get(month_key, Decimal("0")) + amount
        month_counts[month_key] = month_counts.get(month_key, 0) + 1
        iso = created.isocalendar()
        week_key = (iso.year, iso.week)
        week_buckets[week_key] = week_buckets.get(week_key, Decimal("0")) + amount
        year_buckets[created.year] = year_buckets.get(created.year, Decimal("0")) + amount
        client_times.setdefault(user.id, []).append(created)

    month_keys = [shift_month(now.year, now.month, -offset) for offset in range(4, -1, -1)]
    monthly = [MonthPoint(label=months[key[1] - 1], total=quantize_money(month_buckets.get(key, Decimal("0")))) for key in month_keys]
    weekly = []
    for offset in range(4, -1, -1):
        point = now - timedelta(weeks=offset)
        iso = point.isocalendar()
        start = point - timedelta(days=point.weekday())
        weekly.append(
            MonthPoint(label=f"{start.day} {months[start.month - 1]}", total=quantize_money(week_buckets.get((iso.year, iso.week), Decimal("0"))))
        )
    yearly = [
        MonthPoint(label=str(year), total=quantize_money(year_buckets.get(year, Decimal("0"))))
        for year in range(now.year - 4, now.year + 1)
    ]
    company = db.get(Company, company_id)
    target = Decimal(company.monthly_sales_target or 0) if company is not None else Decimal("0")
    current = month_buckets.get((now.year, now.month), Decimal("0"))
    previous_key = shift_month(now.year, now.month, -1)
    previous = month_buckets.get(previous_key, Decimal("0"))
    progress = float((current / target) * 100) if target > 0 else 0.0
    revenue_change = round(float((current - previous) / previous * 100), 1) if previous > 0 else None
    sales_count = month_counts.get((now.year, now.month), 0)
    previous_count = month_counts.get(previous_key, 0)
    count_change = round((sales_count - previous_count) / previous_count * 100, 1) if previous_count > 0 else None
    renewals = 0
    for times in client_times.values():
        ordered_times = sorted(times)
        for created in ordered_times:
            if created.year == now.year and created.month == now.month and created != ordered_times[0]:
                renewals += 1
    today = libya_today()
    subscriptions = db.scalars(select(Subscription).where(Subscription.company_id == company_id)).all()
    active_clients = {row.client_id for row in subscriptions if row.start_date <= today <= row.end_date}
    first_seen: dict[int, datetime] = {}
    for row in subscriptions:
        created = local(row.created_at)
        current_first = first_seen.get(row.client_id)
        if current_first is None or created < current_first:
            first_seen[row.client_id] = created
    new_subscribers = sum(1 for created in first_seen.values() if created.year == now.year and created.month == now.month)
    average = quantize_money(current / sales_count) if sales_count else Decimal("0")
    return CompanyReport(
        sales_total=quantize_money(total),
        profit_total=quantize_money(profit),
        currency=currency,
        commission_percentage=get_settings_view(db).platform_commission_percentage,
        sales=sales,
        monthly_sales=monthly,
        weekly_sales=weekly,
        yearly_sales=yearly,
        monthly_target=quantize_money(target),
        target_progress=round(progress, 1),
        current_month_revenue=quantize_money(current),
        current_month_net=quantize_money(current * (Decimal("1") - Decimal(str(rate)))),
        revenue_change_percent=revenue_change,
        active_subscribers=len(active_clients),
        new_subscribers_this_month=new_subscribers,
        month_sales_count=sales_count,
        sales_count_change_percent=count_change,
        average_ticket=average,
        renewal_rate=round(renewals / sales_count * 100, 1) if sales_count else None,
    )


def platform_performance(db: Session) -> PlatformPerformance:
    rate = Decimal(str(commission_rate(db)))
    currency = get_settings().payment_currency
    payments = db.scalars(select(Payment).where(Payment.status == PaymentStatus.succeeded)).all()
    gross = sum((Decimal(row.amount) for row in payments), Decimal("0"))
    today = libya_today()
    active_subs = db.scalars(select(Subscription)).all()
    active_count = sum(1 for row in active_subs if row.start_date <= today <= row.end_date)
    companies = db.scalars(select(Company).where(Company.status == CompanyStatus.approved)).all()
    clients = db.scalars(select(User).where(User.role == UserRole.client)).all()
    pending = db.scalar(
        select(func.count()).select_from(CompanyJoinRequest).where(CompanyJoinRequest.status == JoinRequestStatus.pending)
    )
    stopped = db.scalar(select(func.count()).select_from(Company).where(Company.status == CompanyStatus.stopped))
    now = datetime.now(timezone.utc)
    previous_month = 12 if now.month == 1 else now.month - 1
    previous_year = now.year - 1 if now.month == 1 else now.year

    def month_gross(year: int, month: int) -> Decimal:
        total = Decimal("0")
        for row in payments:
            created = row.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if created.year == year and created.month == month:
                total += Decimal(row.amount)
        return total

    current_month = month_gross(now.year, now.month)
    last_month = month_gross(previous_year, previous_month)
    change = round(float((current_month - last_month) / last_month * 100), 1) if last_month > 0 else None
    return PlatformPerformance(
        total_gross_sales=quantize_money(gross),
        total_platform_net_revenue=quantize_money(gross * rate),
        currency=currency,
        total_active_companies=len(list(companies)),
        total_registered_clients=len(list(clients)),
        total_active_subscriptions=active_count,
        pending_join_requests=int(pending or 0),
        stopped_companies=int(stopped or 0),
        revenue_change_percent=change,
    )
