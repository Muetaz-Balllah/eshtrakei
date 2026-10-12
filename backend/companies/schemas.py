from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from backend.auth.schemas import PasswordStr
from backend.enums import CompanyStatus, JoinRequestStatus


class CompanyPublic(BaseModel):
    id: int
    name: str
    description: str
    phone: str
    logo_url: str | None


class ManagerCompany(CompanyPublic):
    balance: Decimal


class CompanyAdmin(CompanyPublic):
    status: CompanyStatus
    has_manager: bool


class JoinRequestPublic(BaseModel):
    id: int
    name: str
    description: str
    phone: str
    logo_url: str | None
    status: JoinRequestStatus
    created_at: datetime


class CompanyUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    phone: str = Field(min_length=1, max_length=30)


class CreateManagerRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320)
    password: PasswordStr
