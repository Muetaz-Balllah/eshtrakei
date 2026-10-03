"""company balance, coupon cap, banner approval, financial log"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_manager_growth"
down_revision: Union[str, None] = "0009_avatar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("balance", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("coupons", sa.Column("max_total_uses", sa.Integer(), nullable=True))
    op.add_column("platform_banners", sa.Column("company_id", sa.Integer(), nullable=True))
    op.add_column("platform_banners", sa.Column("status", sa.String(32), nullable=False, server_default="approved"))
    op.add_column("platform_banners", sa.Column("price", sa.Numeric(12, 2), nullable=False, server_default="0"))
    op.add_column("platform_banners", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("platform_banners", sa.Column("reviewed_by", sa.Integer(), nullable=True))
    op.create_table(
        "financial_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("banner_id", sa.Integer(), nullable=True),
        sa.Column("party", sa.String(20), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("note", sa.String(200), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("financial_entries")
    op.drop_column("platform_banners", "reviewed_by")
    op.drop_column("platform_banners", "reviewed_at")
    op.drop_column("platform_banners", "price")
    op.drop_column("platform_banners", "status")
    op.drop_column("platform_banners", "company_id")
    op.drop_column("coupons", "max_total_uses")
    op.drop_column("companies", "balance")
