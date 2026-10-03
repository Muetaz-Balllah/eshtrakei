"""wallet transaction note"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_wallet_note"
down_revision: Union[str, None] = "0007_coupon_uses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("wallet_transactions", sa.Column("note", sa.String(200), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("wallet_transactions", "note")
