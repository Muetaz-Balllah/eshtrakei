from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PurchaseBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_id: int
    package_id: int
    coupon_code: str | None = None
    idempotency_key: str = Field(min_length=8, max_length=80)
    simulated_outcome: Literal["success", "failure"] | None = None
    pay_with_wallet: bool = False


class RenewBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    idempotency_key: str = Field(min_length=8, max_length=80)
    simulated_outcome: Literal["success", "failure"] | None = None
    pay_with_wallet: bool = False


class SubscriptionOut(BaseModel):
    id: int
    company_id: int
    company_name: str
    package_name: str
    start_date: date
    end_date: date
    status: str
    days_remaining: int
    price: Decimal
    currency: str
    duration: str
    data_allowance: str
    speed: str
    data_gb: int
    speed_mbps: int
    upload_mbps: int = 0


class InvoiceOut(BaseModel):
    id: int
    invoice_number: int
    amount_paid: Decimal
    currency: str
    package_name: str
    issued_at: datetime | None = None


class PurchaseResult(BaseModel):
    payment_status: str
    subscription: SubscriptionOut | None = None
    invoice: InvoiceOut | None = None
    message: str


class ClientSubscriptions(BaseModel):
    client_id: int
    full_name: str
    email: str
    subscriptions: list[SubscriptionOut]
