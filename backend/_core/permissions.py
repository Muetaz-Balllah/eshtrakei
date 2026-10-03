from backend.enums import UserRole

ROLE_GUARDS = {
    UserRole.platform_admin: "require_platform_admin",
    UserRole.company_manager: "require_company_manager",
    UserRole.client: "require_client",
}
