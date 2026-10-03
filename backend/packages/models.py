from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base
from backend.enums import DurationUnit


class Package(Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(200))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    duration_amount: Mapped[int] = mapped_column(Integer)
    duration_unit: Mapped[DurationUnit] = mapped_column(Enum(DurationUnit, native_enum=False, length=16))
    data_gb: Mapped[int] = mapped_column(Integer)
    speed_mbps: Mapped[int] = mapped_column(Integer)
    upload_mbps: Mapped[int] = mapped_column(Integer, default=0)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
