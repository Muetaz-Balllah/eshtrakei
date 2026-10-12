from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend._core.deps import Principal, require_client, require_company_manager
from backend.coverage.schemas import TowerBody, TowerOut
from backend.coverage.services import add_tower, list_active, list_company, remove_tower
from backend.db import get_db
from backend.errors import AppError

router = APIRouter(tags=["coverage"])


@router.get("/api/towers", response_model=list[TowerOut])
def public_towers(_principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    return list_active(db)


@router.get("/api/company/towers", response_model=list[TowerOut])
def company_towers(principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return list_company(db, principal.company_id)


@router.post("/api/company/towers", response_model=TowerOut)
def create_tower(body: TowerBody, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return add_tower(db, principal.company_id, body)


@router.delete("/api/company/towers/{tower_id}")
def delete_tower(tower_id: int, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    remove_tower(db, principal.company_id, tower_id)
    return {"code": "deleted", "message": "تم حذف البرج"}
