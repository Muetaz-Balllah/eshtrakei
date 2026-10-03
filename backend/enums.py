from enum import Enum


class UserRole(str, Enum):
    platform_admin = "platform_admin"
    company_manager = "company_manager"
    client = "client"


class CompanyStatus(str, Enum):
    approved = "approved"
    rejected = "rejected"
    stopped = "stopped"


class JoinRequestStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class DurationUnit(str, Enum):
    days = "days"
    months = "months"


class SubscriptionStatus(str, Enum):
    active = "active"
    expired = "expired"


class PaymentStatus(str, Enum):
    succeeded = "succeeded"
    failed = "failed"
