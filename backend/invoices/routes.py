from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend._core.deps import Principal, get_current_principal
from backend.db import get_db
from backend.enums import UserRole
from backend.errors import AppError
from backend.invoices.models import Invoice
from backend.invoices.services import invoice_file
from backend.subscriptions.schemas import InvoiceOut

router = APIRouter(tags=["invoices"])


@router.get("/api/invoices", response_model=list[InvoiceOut])
def my_invoices(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    query = select(Invoice).order_by(Invoice.id.desc())
    if principal.user.role == UserRole.client:
        query = query.where(Invoice.client_id == principal.user.id)
    elif principal.user.role == UserRole.company_manager:
        query = query.where(Invoice.company_id == principal.company_id)
    else:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return [
        InvoiceOut(
            id=row.id,
            invoice_number=row.invoice_number,
            amount_paid=row.amount_paid,
            currency=row.currency,
            package_name=row.package_name_snapshot,
            issued_at=row.issued_at,
        )
        for row in db.scalars(query).all()
    ]


@router.get("/api/subscriptions/{subscription_id}/invoices", response_model=list[InvoiceOut])
def subscription_invoices(
    subscription_id: int,
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(Invoice).where(Invoice.subscription_id == subscription_id)).all()
    if not rows:
        return []
    if principal.user.role == UserRole.client and rows[0].client_id != principal.user.id:
        raise AppError(404, "not_found", "الفاتورة غير موجودة")
    if principal.user.role == UserRole.company_manager and rows[0].company_id != principal.company_id:
        raise AppError(404, "not_found", "الفاتورة غير موجودة")
    if principal.user.role == UserRole.platform_admin:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return [
        InvoiceOut(
            id=row.id,
            invoice_number=row.invoice_number,
            amount_paid=row.amount_paid,
            currency=row.currency,
            package_name=row.package_name_snapshot,
        )
        for row in rows
    ]


@router.get("/api/invoices/{invoice_id}/pdf")
def download_pdf(invoice_id: int, principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)):
    if principal.user.role == UserRole.client:
        path = invoice_file(db, invoice_id, principal.user.id, None)
    elif principal.user.role == UserRole.company_manager:
        path = invoice_file(db, invoice_id, None, principal.company_id)
    else:
        raise AppError(403, "forbidden", "ليست لديك صلاحية لهذا الإجراء")
    return FileResponse(path, media_type="application/pdf", filename=path.name)
