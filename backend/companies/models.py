from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db import Base
from backend.enums import CompanyStatus, JoinRequestStatus


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    phone: Mapped[str] = mapped_column(String(30))
    logo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[CompanyStatus] = mapped_column(Enum(CompanyStatus, native_enum=False, length=32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    monthly_sales_target: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))


class CompanyManager(Base):
    __tablename__ = "company_managers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CompanyJoinRequest(Base):
    __tablename__ = "company_join_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    phone: Mapped[str] = mapped_column(String(30))
    logo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[JoinRequestStatus] = mapped_column(Enum(JoinRequestStatus, native_enum=False, length=32))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
