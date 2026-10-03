from dataclasses import dataclass

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend._core.redis_client import token_exists
from backend._core.security import decode_access_token
from backend.auth.models import User
from backend.db import get_db
from backend.enums import UserRole
from backend.errors import AppError

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class Principal:
    user: User
    company_id: int | None
    jti: str


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(401, "unauthorized", "يلزم تسجيل الدخول")
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise AppError(401, "unauthorized", "يلزم تسجيل الدخول") from exc
    jti = payload.get("jti")
    if not jti or not token_exists(jti):
        raise AppError(401, "unauthorized", "يلزم تسجيل الدخول")
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise AppError(401, "unauthorized", "يلزم تسجيل الدخول")
    company_id = payload.get("company_id")
    return Principal(user=user, company_id=company_id, jti=jti)


def require_platform_admin(principal: Principal = Depends(get_current_principal)) -> Principal:
    if principal.user.role != UserRole.platform_admin:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return principal


def require_company_manager(principal: Principal = Depends(get_current_principal)) -> Principal:
    if principal.user.role != UserRole.company_manager:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return principal


def require_client(principal: Principal = Depends(get_current_principal)) -> Principal:
    if principal.user.role != UserRole.client:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return principal
