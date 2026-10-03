from pydantic import BaseModel, Field

from backend.enums import UserRole


class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=30)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    role: UserRole
    full_name: str


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    city: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=30)


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class MeResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole
    company_id: int | None
    city: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
