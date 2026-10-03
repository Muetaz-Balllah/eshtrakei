from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.notifications.models import Notification
from backend.notifications.schemas import NotificationOut
from backend.subscriptions.models import Subscription
from backend.settings.services import warning_days
from backend.utils import libya_today, utc_now


def run_expiry_check(db: Session) -> int:
    today = libya_today()
    thresholds = {day: f"expiry_{day}_days" for day in warning_days(db)}
    created = 0
    rows = db.scalars(select(Subscription)).all()
    for row in rows:
        remaining = (row.end_date - today).days
        if today > row.end_date:
            row.status = "expired"
        kind = thresholds.get(remaining)
        if kind is None:
            continue
        exists = db.scalar(
            select(Notification.id).where(Notification.subscription_id == row.id, Notification.kind == kind)
        )
        if exists is not None:
            continue
        push(db, row.client_id, kind, f"اشتراك {row.package_name_snapshot} ينتهي خلال {remaining} يوم", row.id)
        push_company_manager(db, row.company_id, f"{kind}_{row.id}", f"اشتراك {row.package_name_snapshot} لدى أحد المشتركين ينتهي خلال {remaining} يوم")
        created += 1
    db.commit()
    return created


def push(db: Session, user_id: int, kind: str, message: str, subscription_id: int | None = None) -> None:
    db.add(
        Notification(
            client_id=user_id,
            subscription_id=subscription_id,
            kind=kind[:64],
            message=message,
            is_read=False,
            created_at=utc_now(),
        )
    )


def push_role(db: Session, role, kind: str, message: str) -> None:
    from backend.auth.models import User

    users = db.scalars(select(User.id).where(User.role == role)).all()
    for user_id in users:
        push(db, user_id, kind, message)


def push_company_manager(db: Session, company_id: int, kind: str, message: str) -> None:
    from backend.companies.models import CompanyManager

    link = db.scalar(select(CompanyManager).where(CompanyManager.company_id == company_id))
    if link is not None:
        push(db, link.user_id, kind, message)


def list_for_user(db: Session, user_id: int) -> list[NotificationOut]:
    rows = db.scalars(
        select(Notification).where(Notification.client_id == user_id).order_by(Notification.created_at.desc())
    )
    return [
        NotificationOut(id=row.id, message=row.message, kind=row.kind, is_read=row.is_read, created_at=row.created_at)
        for row in rows
    ]


def mark_read(db: Session, user_id: int) -> None:
    rows = db.scalars(select(Notification).where(Notification.client_id == user_id, Notification.is_read.is_(False))).all()
    for row in rows:
        row.is_read = True
    db.commit()
