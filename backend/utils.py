import calendar
from datetime import UTC, date, datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

LIBYA = ZoneInfo("Africa/Tripoli")


def utc_now() -> datetime:
    return datetime.now(UTC)


def libya_today() -> date:
    return datetime.now(LIBYA).date()


def quantize_money(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
