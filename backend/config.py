from functools import lru_cache

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    database_url: str = "sqlite:///./backend/dev.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me"
    access_token_ttl_seconds: int = 86400
    platform_admin_email: str = "admin@eshtrakei.local"
    platform_admin_password: str = ""
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    payment_provider: str = "mock"
    payment_currency: str = "LYD"
    email_backend: str = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    invoice_storage_dir: str = "backend/storage/invoices"
    storage_endpoint_url: str = Field(default="", validation_alias=AliasChoices("AWS_ENDPOINT_URL_S3", "STORAGE_ENDPOINT_URL"))
    storage_access_key_id: str = Field(default="", validation_alias=AliasChoices("AWS_ACCESS_KEY_ID", "STORAGE_ACCESS_KEY_ID"))
    storage_secret_access_key: str = Field(
        default="", validation_alias=AliasChoices("AWS_SECRET_ACCESS_KEY", "STORAGE_SECRET_ACCESS_KEY")
    )
    storage_region: str = Field(default="", validation_alias=AliasChoices("AWS_REGION", "STORAGE_REGION"))
    storage_bucket: str = Field(default="eshtrakei-files", validation_alias=AliasChoices("S3_BUCKET", "STORAGE_BUCKET"))

    @model_validator(mode="after")
    def use_psycopg_for_postgres(self) -> "Settings":
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql://" + url.removeprefix("postgres://")
        if url.startswith("postgresql://"):
            self.database_url = "postgresql+psycopg://" + url.removeprefix("postgresql://")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
