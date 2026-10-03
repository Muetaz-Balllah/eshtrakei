from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CouponCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    discount_amount: Decimal = Field(gt=0)
    expires_at: datetime
    max_uses: int | None = Field(default=None, gt=0)
    max_total_uses: int | None = Field(default=None, gt=0)


class CouponOut(BaseModel):
    id: int
    code: str
    discount_amount: Decimal
    expires_at: datetime
    currency: str
    max_uses: int | None = None
    max_total_uses: int | None = None
    redemption_count: int = 0
