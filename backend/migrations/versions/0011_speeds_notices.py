"""package upload speed and readable notifications"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_speeds_notices"
down_revision: Union[str, None] = "0010_manager_growth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("packages", sa.Column("upload_mbps", sa.Integer(), nullable=False, server_default="0"))
    op.execute("UPDATE packages SET upload_mbps = speed_mbps")
    with op.batch_alter_table("notifications") as batch:
        batch.alter_column("subscription_id", existing_type=sa.Integer(), nullable=True)
        batch.alter_column("kind", existing_type=sa.String(64), type_=sa.String(64))
        batch.add_column(sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    with op.batch_alter_table("notifications") as batch:
        batch.drop_column("is_read")
    op.drop_column("packages", "upload_mbps")
