from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.companies.models import Company
from backend.coverage.models import Tower
from backend.coverage.schemas import TowerBody, TowerOut
from backend.errors import AppError


def _out(db: Session, row: Tower) -> TowerOut:
    company = db.get(Company, row.company_id)
    return TowerOut(
        id=row.id,
        company_id=row.company_id,
        company_name=company.name if company else "",
        name=row.name,
        latitude=row.latitude,
        longitude=row.longitude,
        radius_meters=row.radius_meters,
        is_active=row.is_active,
    )


def list_company(db: Session, company_id: int) -> list[TowerOut]:
    rows = db.scalars(select(Tower).where(Tower.company_id == company_id).order_by(Tower.id.desc())).all()
    return [_out(db, row) for row in rows]


def list_active(db: Session) -> list[TowerOut]:
    rows = db.scalars(select(Tower).where(Tower.is_active.is_(True)).order_by(Tower.company_id, Tower.id)).all()
    return [_out(db, row) for row in rows]


def add_tower(db: Session, company_id: int, body: TowerBody) -> TowerOut:
    row = Tower(
        company_id=company_id,
        name=body.name.strip(),
        latitude=body.latitude,
        longitude=body.longitude,
        radius_meters=body.radius_meters,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _out(db, row)


def remove_tower(db: Session, company_id: int, tower_id: int) -> None:
    row = db.get(Tower, tower_id)
    if row is None or row.company_id != company_id:
        raise AppError(404, "not_found", "البرج غير موجود")
    db.delete(row)
    db.commit()
