"""platform settings"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_settings"
down_revision: Union[str, None] = "0004_notices"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "platform_settings",
        sa.Column("key", sa.String(80), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.bulk_insert(
        sa.table("platform_settings", sa.column("key", sa.String), sa.column("value", sa.Text)),
        [
            {"key": "platform_commission_percentage", "value": "5.0"},
            {"key": "allow_company_registration", "value": "true"},
            {"key": "expiry_warning_days", "value": "3,1"},
            {"key": "support_email", "value": "support@platform.ly"},
        ],
    )


def downgrade() -> None:
    op.drop_table("platform_settings")
