from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class PaymentRequest(BaseModel):
    amount: Decimal
    currency: str
    idempotency_key: str
    client_id: int
    company_id: int
    description: str
    simulated_outcome: Literal["success", "failure"] | None = None


class PaymentResult(BaseModel):
    status: Literal["succeeded", "failed"]
    provider_reference: str
    failure_code: str | None = None
