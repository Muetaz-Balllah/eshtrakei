from uuid import uuid4

from backend.config import get_settings
from backend.errors import AppError
from backend.payments.schemas import PaymentRequest, PaymentResult


class MockPaymentProvider:
    name = "mock"

    def charge(self, request: PaymentRequest) -> PaymentResult:
        if request.simulated_outcome == "success":
            return PaymentResult(status="succeeded", provider_reference=f"mock_{uuid4().hex}")
        if request.simulated_outcome == "failure":
            return PaymentResult(status="failed", provider_reference=f"mock_{uuid4().hex}", failure_code="mock_declined")
        raise AppError(400, "invalid_outcome", "يجب تحديد نتيجة الدفع التجريبية")


def get_payment_provider() -> MockPaymentProvider:
    settings = get_settings()
    if settings.payment_provider == "mock":
        return MockPaymentProvider()
    raise AppError(500, "payment_provider", "مزود الدفع غير مهيأ")
