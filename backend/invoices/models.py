from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_number: Mapped[int] = mapped_column(Integer, unique=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), unique=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"))
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    company_name_snapshot: Mapped[str] = mapped_column(String(200))
    client_name_snapshot: Mapped[str] = mapped_column(String(200))
    client_email_snapshot: Mapped[str] = mapped_column(String(320))
    package_name_snapshot: Mapped[str] = mapped_column(String(200))
    duration_snapshot: Mapped[str] = mapped_column(String(40))
    data_allowance_snapshot: Mapped[str] = mapped_column(String(40))
    speed_snapshot: Mapped[str] = mapped_column(String(40))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8))
    pdf_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
