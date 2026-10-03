from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class MonthPoint(BaseModel):
    label: str
    total: Decimal


class SaleRow(BaseModel):
    created_at: datetime
    client_name: str
    package_name: str
    amount: Decimal
    currency: str


class CompanyReport(BaseModel):
    sales_total: Decimal
    profit_total: Decimal
    currency: str
    commission_percentage: float
    sales: list[SaleRow]
    monthly_sales: list[MonthPoint]
    weekly_sales: list[MonthPoint] = []
    yearly_sales: list[MonthPoint] = []
    monthly_target: Decimal
    target_progress: float
    current_month_revenue: Decimal = Decimal("0")
    current_month_net: Decimal = Decimal("0")
    revenue_change_percent: float | None = None
    active_subscribers: int = 0
    new_subscribers_this_month: int = 0
    month_sales_count: int = 0
    sales_count_change_percent: float | None = None
    average_ticket: Decimal = Decimal("0")
    renewal_rate: float | None = None


class PlatformPerformance(BaseModel):
    total_gross_sales: Decimal
    total_platform_net_revenue: Decimal
    currency: str
    total_active_companies: int
    total_registered_clients: int
    total_active_subscriptions: int
    pending_join_requests: int = 0
    stopped_companies: int = 0
    revenue_change_percent: float | None = None
