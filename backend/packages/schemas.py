from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from backend.enums import DurationUnit


class PackageBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    price: Decimal = Field(gt=0)
    duration_amount: int = Field(gt=0)
    duration_unit: DurationUnit = DurationUnit.days
    data_gb: int = Field(gt=0)
    speed_mbps: int | None = Field(default=None, gt=0)
    download_mbps: int | None = Field(default=None, gt=0)
    upload_mbps: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def normalize(self):
        if self.duration_unit == DurationUnit.months:
            self.duration_amount = self.duration_amount * 30
            self.duration_unit = DurationUnit.days
        download = self.download_mbps or self.speed_mbps
        upload = self.upload_mbps or download
        if download is None or upload is None:
            raise ValueError("يجب تحديد سرعة التحميل وسرعة الرفع")
        self.download_mbps = download
        self.speed_mbps = download
        self.upload_mbps = upload
        return self


class PackageOut(BaseModel):
    id: int
    company_id: int
    name: str
    price: Decimal
    duration_amount: int
    duration_unit: DurationUnit
    data_gb: int
    speed_mbps: int
    download_mbps: int
    upload_mbps: int
    is_available: bool
    currency: str
    active_subscribers: int = 0
