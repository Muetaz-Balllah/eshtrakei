"""optional coupon usage cap"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_coupon_uses"
down_revision: Union[str, None] = "0006_growth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("coupons", sa.Column("max_uses", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("coupons", "max_uses")
