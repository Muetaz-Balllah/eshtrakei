from sqlalchemy.orm import Session

from backend.errors import AppError
from backend.settings.models import PlatformSetting
from backend.settings.schemas import SettingsOut, SettingsUpdate
from backend.utils import utc_now

DEFAULTS = {
    "platform_commission_percentage": "5.0",
    "allow_company_registration": "true",
    "expiry_warning_days": "3,1",
    "support_email": "support@platform.ly",
    "banner_price": "50.00",
}


def ensure_defaults(db: Session) -> None:
    for key, value in DEFAULTS.items():
        if db.get(PlatformSetting, key) is None:
            db.add(PlatformSetting(key=key, value=value))
    db.commit()


def _value(db: Session, key: str) -> str:
    row = db.get(PlatformSetting, key)
    if row is None:
        ensure_defaults(db)
        row = db.get(PlatformSetting, key)
    return row.value if row else DEFAULTS[key]


def get_settings_view(db: Session) -> SettingsOut:
    ensure_defaults(db)
    return SettingsOut(
        platform_commission_percentage=float(_value(db, "platform_commission_percentage")),
        allow_company_registration=_value(db, "allow_company_registration") == "true",
        expiry_warning_days=[int(part) for part in _value(db, "expiry_warning_days").split(",") if part],
        support_email=_value(db, "support_email"),
        banner_price=float(_value(db, "banner_price")),
    )


def update_settings(db: Session, body: SettingsUpdate, admin_id: int) -> SettingsOut:
    if any(day <= 0 for day in body.expiry_warning_days):
        raise AppError(400, "invalid_setting", "أيام التنبيه يجب أن تكون أكبر من صفر")
    values = {
        "platform_commission_percentage": str(body.platform_commission_percentage),
        "allow_company_registration": "true" if body.allow_company_registration else "false",
        "expiry_warning_days": ",".join(str(day) for day in body.expiry_warning_days),
        "support_email": body.support_email.strip(),
    }
    if body.banner_price is not None:
        values["banner_price"] = str(body.banner_price)
    now = utc_now()
    for key, value in values.items():
        row = db.get(PlatformSetting, key)
        if row is None:
            db.add(PlatformSetting(key=key, value=value, updated_at=now, updated_by=admin_id))
        else:
            row.value = value
            row.updated_at = now
            row.updated_by = admin_id
    db.commit()
    return get_settings_view(db)


def commission_rate(db: Session) -> float:
    return float(_value(db, "platform_commission_percentage")) / 100


def registration_open(db: Session) -> bool:
    return _value(db, "allow_company_registration") == "true"


def warning_days(db: Session) -> list[int]:
    return [int(part) for part in _value(db, "expiry_warning_days").split(",") if part]


def support_email(db: Session) -> str:
    return _value(db, "support_email")


def banner_price(db: Session):
    from decimal import Decimal

    from backend.utils import quantize_money

    return quantize_money(Decimal(_value(db, "banner_price") or "0"))
