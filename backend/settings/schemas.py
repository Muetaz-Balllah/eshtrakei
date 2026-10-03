from pydantic import BaseModel, Field


class SettingsOut(BaseModel):
    platform_commission_percentage: float
    allow_company_registration: bool
    expiry_warning_days: list[int]
    support_email: str
    banner_price: float


class SettingsUpdate(BaseModel):
    platform_commission_percentage: float = Field(ge=0, le=100)
    allow_company_registration: bool
    expiry_warning_days: list[int] = Field(min_length=1)
    support_email: str = Field(min_length=3, max_length=320)
    banner_price: float | None = Field(default=None, ge=0)
