from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.config import get_settings
from backend.db import Base
from backend.advertisements import models as advertisement_models  # noqa: F401
from backend.auth import models as auth_models  # noqa: F401
from backend.companies import models as company_models  # noqa: F401
from backend.complaints import models as complaint_models  # noqa: F401
from backend.coupons import models as coupon_models  # noqa: F401
from backend.invoices import models as invoice_models  # noqa: F401
from backend.notifications import models as notification_models  # noqa: F401
from backend.packages import models as package_models  # noqa: F401
from backend.payments import models as payment_models  # noqa: F401
from backend.settings import models as settings_models  # noqa: F401
from backend.subscriptions import models as subscription_models  # noqa: F401
from backend.wallets import models as wallet_models  # noqa: F401
from backend.banners import models as banner_models  # noqa: F401
from backend.coverage import models as coverage_models  # noqa: F401
from backend.finance import models as finance_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=get_settings().database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
