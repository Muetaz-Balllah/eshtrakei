from datetime import UTC, datetime, timedelta
from uuid import uuid4

import re

import bcrypt
import jwt

from backend.config import get_settings

_LETTER = re.compile(r"[A-Za-z\u0600-\u06FF]")
_DIGIT = re.compile(r"\d")
PASSWORD_RULE_MESSAGE = "كلمة المرور يجب أن تكون 8 أحرف على الأقل وتحتوي على حروف وأرقام"


def assert_strong_password(password: str) -> str:
    if not (8 <= len(password) <= 128 and _LETTER.search(password) and _DIGIT.search(password)):
        raise ValueError(PASSWORD_RULE_MESSAGE)
    return password


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(*, user_id: int, role: str, company_id: int | None) -> tuple[str, str]:
    settings = get_settings()
    jti = str(uuid4())
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.access_token_ttl_seconds)
    payload = {
        "sub": str(user_id),
        "role": role,
        "company_id": company_id,
        "jti": jti,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, jti


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
