import logging
from datetime import UTC
from pathlib import Path
from zoneinfo import ZoneInfo

from arabic_reshaper import reshape
from bidi.algorithm import get_display
from fpdf import FPDF
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.errors import AppError
from backend.invoices.models import Invoice

logger = logging.getLogger(__name__)
FONT = Path(__file__).resolve().parents[1] / "_core" / "fonts" / "NotoNaskhArabic-Regular.ttf"
NAVY = (33, 49, 69)
ORANGE = (245, 130, 32)
INK = (11, 28, 48)
MUTED = (90, 107, 130)
PAPER = (248, 249, 255)
LINE = (220, 228, 240)
LIBYA = ZoneInfo("Africa/Tripoli")
MONTHS = (
    "يناير",
    "فبراير",
    "مارس",
    "أبريل",
    "مايو",
    "يونيو",
    "يوليو",
    "أغسطس",
    "سبتمبر",
    "أكتوبر",
    "نوفمبر",
    "ديسمبر",
)


def _visual(text: object) -> str:
    value = str(text)
    if any("\u0600" <= char <= "\u06FF" for char in value):
        return get_display(reshape(value))
    return value


def _place(pdf: FPDF, x: float, y: float, width: float, text: object, size: float, color: tuple[int, int, int], *, right: bool) -> None:
    pdf.set_font("Naskh", size=size)
    pdf.set_text_color(*color)
    visual = _visual(text)
    text_width = min(pdf.get_string_width(visual), width - 8)
    origin = x + width - text_width - 4 if right else x + 4
    pdf.set_xy(origin, y)
    pdf.cell(text_width + 1, size * 0.55, visual)


def _issued_label(invoice: Invoice) -> str:
    issued = invoice.issued_at
    if issued.tzinfo is None:
        issued = issued.replace(tzinfo=UTC)
    local = issued.astimezone(LIBYA)
    return f"{local.day} {MONTHS[local.month - 1]} {local.year}  {local.strftime('%H:%M')}"


def _money(invoice: Invoice) -> str:
    unit = "د.ل" if str(invoice.currency).upper() in {"LYD", "د.ل"} else str(invoice.currency)
    return f"{invoice.amount_paid} {unit}"


def render_invoice_pdf(invoice: Invoice) -> str:
    settings = get_settings()
    target_dir = Path(settings.invoice_storage_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"invoice-{invoice.invoice_number}.pdf"
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()
    pdf.add_font("Naskh", "", str(FONT))
    pdf.set_fill_color(*PAPER)
    pdf.rect(0, 0, 210, 297, style="F")

    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 210, 42, style="F")
    pdf.set_fill_color(*ORANGE)
    pdf.rect(0, 42, 210, 3, style="F")
    _place(pdf, 108, 10, 90, "اشتراكي", 22, (255, 255, 255), right=True)
    _place(pdf, 108, 22, 90, "فاتورة اشتراك إنترنت", 12, (255, 213, 186), right=True)
    _place(pdf, 14, 10, 80, f"رقم {invoice.invoice_number}", 16, (255, 255, 255), right=False)
    _place(pdf, 14, 22, 80, "فاتورة مدفوعة", 11, (255, 213, 186), right=False)

    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(*LINE)
    pdf.rect(14, 54, 182, 16, style="DF", round_corners=True, corner_radius=3)
    _place(pdf, 100, 58, 90, f"تاريخ الإصدار: {_issued_label(invoice)}", 11, INK, right=True)

    pdf.rect(108, 76, 88, 42, style="DF", round_corners=True, corner_radius=3)
    pdf.rect(14, 76, 88, 42, style="DF", round_corners=True, corner_radius=3)
    _place(pdf, 112, 80, 80, "الشركة", 10, ORANGE, right=True)
    _place(pdf, 112, 90, 80, invoice.company_name_snapshot, 13, INK, right=True)
    _place(pdf, 18, 80, 80, "الزبون", 10, ORANGE, right=True)
    _place(pdf, 18, 90, 80, invoice.client_name_snapshot, 13, INK, right=True)
    _place(pdf, 18, 100, 80, invoice.client_email_snapshot, 10, MUTED, right=False)

    _place(pdf, 14, 128, 182, "تفاصيل الباقة", 13, NAVY, right=True)
    rows = (
        ("الباقة", invoice.package_name_snapshot),
        ("المدة", invoice.duration_snapshot),
        ("حجم البيانات", invoice.data_allowance_snapshot),
        ("السرعة", invoice.speed_snapshot),
    )
    y = 136
    for index, (label, value) in enumerate(rows):
        pdf.set_fill_color(255, 255, 255) if index % 2 == 0 else pdf.set_fill_color(239, 244, 255)
        pdf.rect(14, y, 182, 12, style="F")
        _place(pdf, 110, y + 2.5, 82, label, 11, MUTED, right=True)
        _place(pdf, 18, y + 2.5, 88, value, 11, INK, right=False)
        y += 12

    pdf.set_fill_color(*NAVY)
    pdf.rect(14, y + 8, 182, 24, style="F", round_corners=True, corner_radius=3)
    _place(pdf, 100, y + 14, 90, "المبلغ المدفوع", 12, (255, 255, 255), right=True)
    _place(pdf, 18, y + 13, 80, _money(invoice), 16, (255, 213, 186), right=False)

    pdf.set_draw_color(*LINE)
    pdf.line(14, 268, 196, 268)
    _place(pdf, 14, 274, 182, "صادرة إلكترونياً من منصة اشتراكي، ولا تحتاج إلى توقيع.", 10, MUTED, right=True)
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
