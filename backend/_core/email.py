import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path

from backend.config import get_settings

logger = logging.getLogger(__name__)


def send_purchase_confirmation(to: str, subject: str, body: str, pdf_path: str | None) -> None:
    settings = get_settings()
    if settings.email_backend == "console":
        logger.warning("purchase email to=%s subject=%s attachment=%s\n%s", to, subject, pdf_path, body)
        return
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from or settings.smtp_user
    message["To"] = to
    message.set_content(body)
    if pdf_path and Path(pdf_path).is_file():
        data = Path(pdf_path).read_bytes()
        message.add_attachment(data, maintype="application", subtype="pdf", filename=Path(pdf_path).name)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_user:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
