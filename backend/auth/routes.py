from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend._core.deps import Principal, get_current_principal
from backend.auth.models import User
from backend.auth.schemas import AuthResponse, LoginRequest, MeResponse, PasswordUpdate, ProfileUpdate, RegisterRequest
from backend.auth.services import change_password, login, logout, register_client, save_avatar, update_profile
from backend.companies.services import logo_url
from backend.db import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register_route(body: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    token, user = register_client(db, body)
    return AuthResponse(access_token=token, role=user.role, full_name=user.full_name)


@router.post("/login", response_model=AuthResponse)
def login_route(body: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    token, user = login(db, str(body.email), body.password)
    role = user.role
    return AuthResponse(access_token=token, role=role, full_name=user.full_name)


@router.post("/logout")
def logout_route(principal: Principal = Depends(get_current_principal)) -> dict:
    logout(principal.jti)
    return {"code": "logged_out", "message": "تم تسجيل الخروج"}


def _me(user: User, company_id: int | None) -> MeResponse:
    return MeResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        company_id=company_id,
        city=user.city,
        phone=user.phone,
        avatar_url=logo_url(user.avatar_path),
    )


@router.get("/me", response_model=MeResponse)
def me_route(principal: Principal = Depends(get_current_principal)) -> MeResponse:
    return _me(principal.user, principal.company_id)


@router.put("/profile", response_model=MeResponse)
def profile_route(body: ProfileUpdate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> MeResponse:
    user = update_profile(db, principal.user, body.full_name, body.city, body.phone)
    return _me(user, principal.company_id)


@router.post("/avatar", response_model=MeResponse)
async def avatar_route(
    image: UploadFile = File(),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> MeResponse:
    user = await save_avatar(db, principal.user, image)
    return _me(user, principal.company_id)


@router.post("/password")
def password_route(body: PasswordUpdate, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    change_password(db, principal.user, body.current_password, body.new_password)
    return {"code": "updated", "message": "تم تغيير كلمة المرور"}
