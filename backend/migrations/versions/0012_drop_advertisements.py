"""drop the separate advertisements table; banners are the only ads"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_drop_advertisements"
down_revision: Union[str, None] = "0011_speeds_notices"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("advertisements")


def downgrade() -> None:
    op.create_table(
        "advertisements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("image_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
