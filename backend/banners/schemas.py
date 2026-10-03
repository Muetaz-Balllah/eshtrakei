from decimal import Decimal

from pydantic import BaseModel


class BannerOut(BaseModel):
    id: int
    title: str
    body: str
    image_url: str | None
    is_active: bool
    status: str
    price: Decimal
    company_id: int | None = None
    company_name: str = ""
    company_balance: Decimal | None = None


class LedgerOut(BaseModel):
    id: int
    company_id: int | None
    company_name: str
    banner_id: int | None
    party: str
    kind: str
    amount: Decimal
    note: str
    created_at: str
