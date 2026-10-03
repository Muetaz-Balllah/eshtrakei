"""user profile picture"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_avatar"
down_revision: Union[str, None] = "0008_wallet_note"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_path", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_path")
