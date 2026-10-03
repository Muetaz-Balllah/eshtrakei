from sqlalchemy import select
from sqlalchemy.orm import Session

from backend._core.redis_client import delete_token, store_token
from backend._core.security import create_access_token, hash_password, verify_password
from backend.auth.models import User
from backend.auth.schemas import RegisterRequest
from backend.companies.models import Company, CompanyManager
from backend.config import get_settings
from backend.enums import CompanyStatus, UserRole
from backend.errors import AppError
from backend.utils import utc_now


def issue_token(db: Session, user: User) -> str:
    company_id = None
    if user.role == UserRole.company_manager:
        link = db.scalar(select(CompanyManager).where(CompanyManager.user_id == user.id))
        if link is None:
            raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
        company = db.get(Company, link.company_id)
        if company is None or company.status == CompanyStatus.stopped:
            raise AppError(403, "company_stopped", "تم إيقاف هذه الشركة ولا يمكن تسجيل الدخول")
        company_id = company.id
    token, jti = create_access_token(user_id=user.id, role=user.role.value, company_id=company_id)
    store_token(jti, user.id, get_settings().access_token_ttl_seconds)
    return token


def login(db: Session, email: str, password: str) -> tuple[str, User]:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise AppError(401, "invalid_credentials", "البريد الإلكتروني أو كلمة المرور غير صحيحة")
    return issue_token(db, user), user


def update_profile(db: Session, user: User, full_name: str, city: str | None = None, phone: str | None = None) -> User:
    user.full_name = full_name.strip()
    if city is not None:
        user.city = city.strip()
    if phone is not None:
        user.phone = phone.strip()
    db.commit()
    db.refresh(user)
    return user


async def save_avatar(db: Session, user: User, upload) -> User:
    from backend.companies.services import save_image

    path = await save_image(upload, "avatars")
    if path is None:
        raise AppError(400, "invalid_image", "صيغة الصورة يجب أن تكون PNG أو JPG أو WEBP")
    user.avatar_path = path
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise AppError(400, "invalid_password", "كلمة المرور الحالية غير صحيحة")
    user.password_hash = hash_password(new_password)
    db.commit()


def register_client(db: Session, body: RegisterRequest) -> tuple[str, User]:
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise AppError(409, "email_taken", "هذا البريد الإلكتروني مستخدم بالفعل")
    user = User(
        full_name=body.full_name.strip(),
        city=body.city.strip(),
        phone=body.phone.strip(),
        email=email,
        password_hash=hash_password(body.password),
        role=UserRole.client,
        is_active=True,
        created_at=utc_now(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return issue_token(db, user), user


def logout(jti: str) -> None:
    delete_token(jti)
