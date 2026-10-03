from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class TopUpBody(BaseModel):
    amount: Decimal = Field(gt=0)
    simulated_outcome: Literal["success", "failure"] | None = None


class WalletTxOut(BaseModel):
    id: int
    amount: Decimal
    kind: str
    note: str = ""
    created_at: datetime


class WalletOut(BaseModel):
    balance: Decimal
    currency: str
    transactions: list[WalletTxOut]
