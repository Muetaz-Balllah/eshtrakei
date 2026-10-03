from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base
from backend.enums import SubscriptionStatus


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    package_id: Mapped[int] = mapped_column(ForeignKey("packages.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[SubscriptionStatus] = mapped_column(String(16))
    package_name_snapshot: Mapped[str] = mapped_column(String(200))
    price_snapshot: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    duration_snapshot: Mapped[str] = mapped_column(String(40))
    data_allowance_snapshot: Mapped[str] = mapped_column(String(40))
    speed_snapshot: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
