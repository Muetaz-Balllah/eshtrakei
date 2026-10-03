import logging
from pathlib import Path

from arabic_reshaper import reshape
from bidi.algorithm import get_display
from fpdf import FPDF
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.errors import AppError
from backend.invoices.models import Invoice

logger = logging.getLogger(__name__)
FONT = Path("backend/_core/fonts/NotoNaskhArabic-Regular.ttf")


def _ar(text: str) -> str:
    return get_display(reshape(text))


def render_invoice_pdf(invoice: Invoice) -> str:
    settings = get_settings()
    target_dir = Path(settings.invoice_storage_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"invoice-{invoice.invoice_number}.pdf"
    pdf = FPDF()
    pdf.add_page()
    if FONT.is_file():
        pdf.add_font("Naskh", "", str(FONT))
        pdf.set_font("Naskh", size=16)
    else:
        pdf.set_font("Helvetica", size=16)
    lines = [
        f"فاتورة رقم {invoice.invoice_number}",
        f"الشركة: {invoice.company_name_snapshot}",
        f"الزبون: {invoice.client_name_snapshot}",
        f"البريد: {invoice.client_email_snapshot}",
        f"الباقة: {invoice.package_name_snapshot}",
        f"المدة: {invoice.duration_snapshot}",
        f"الحجم: {invoice.data_allowance_snapshot}",
        f"السرعة: {invoice.speed_snapshot}",
        f"المبلغ: {invoice.amount_paid} {invoice.currency}",
    ]
    for line in lines:
        pdf.cell(0, 12, _ar(line) if FONT.is_file() else line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))
    return str(path)


def deliver_invoice(db: Session, invoice: Invoice) -> None:
    try:
        invoice.pdf_path = render_invoice_pdf(invoice)
        db.commit()
    except Exception:
        logger.exception("invoice pdf failed for %s", invoice.id)
        db.rollback()
    try:
        from backend._core.email import send_purchase_confirmation

        subject = f"تأكيد شراء فاتورة {invoice.invoice_number}"
        body = (
            f"تم شراء باقة {invoice.package_name_snapshot} من {invoice.company_name_snapshot}.\n"
            f"المدة: {invoice.duration_snapshot}\n"
            f"المبلغ: {invoice.amount_paid} {invoice.currency}\n"
            f"رقم الفاتورة: {invoice.invoice_number}"
        )
        send_purchase_confirmation(invoice.client_email_snapshot, subject, body, invoice.pdf_path)
    except Exception:
        logger.exception("purchase email failed for %s", invoice.id)


def invoice_file(db: Session, invoice_id: int, client_id: int | None, company_id: int | None) -> Path:
    row = db.get(Invoice, invoice_id)
    if row is None:
        raise AppError(404, "not_found", "الفاتورة غير موجودة")
    if client_id is not None and row.client_id != client_id:
        raise AppError(404, "not_found", "الفاتورة غير موجودة")
    if company_id is not None and row.company_id != company_id:
        raise AppError(404, "not_found", "الفاتورة غير موجودة")
    if not row.pdf_path or not Path(row.pdf_path).is_file():
        raise AppError(404, "not_found", "ملف الفاتورة غير متوفر")
    return Path(row.pdf_path)
