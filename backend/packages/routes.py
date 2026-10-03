from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend._core.deps import Principal, require_client, require_company_manager
from backend.db import get_db
from backend.errors import AppError
from backend.packages.schemas import PackageBody, PackageOut
from backend.packages.services import (
    create_package,
    delete_package,
    list_for_client,
    list_for_manager,
    resume_package,
    stop_package,
    update_package,
)

router = APIRouter(tags=["packages"])


def _company_id(principal: Principal) -> int:
    if principal.company_id is None:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return principal.company_id


@router.get("/api/company/packages", response_model=list[PackageOut])
def manager_packages(principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    return list_for_manager(db, _company_id(principal))


@router.post("/api/company/packages", response_model=PackageOut)
def add_package(body: PackageBody, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    return create_package(db, _company_id(principal), body)


@router.patch("/api/company/packages/{package_id}", response_model=PackageOut)
def edit_package(
    package_id: int,
    body: PackageBody,
    principal: Principal = Depends(require_company_manager),
    db: Session = Depends(get_db),
):
    return update_package(db, _company_id(principal), package_id, body)


@router.post("/api/company/packages/{package_id}/resume", response_model=PackageOut)
def show_package(package_id: int, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    return resume_package(db, _company_id(principal), package_id)


@router.post("/api/company/packages/{package_id}/stop", response_model=PackageOut)
def hide_package(package_id: int, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    return stop_package(db, _company_id(principal), package_id)


@router.delete("/api/company/packages/{package_id}")
def remove_package(package_id: int, principal: Principal = Depends(require_company_manager), db: Session = Depends(get_db)):
    return delete_package(db, _company_id(principal), package_id)


@router.get("/api/companies/{company_id}/packages", response_model=list[PackageOut])
def client_packages(company_id: int, _principal: Principal = Depends(require_client), db: Session = Depends(get_db)):
    return list_for_client(db, company_id)
