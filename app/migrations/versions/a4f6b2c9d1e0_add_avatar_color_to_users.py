"""add avatar color to users

Revision ID: a4f6b2c9d1e0
Revises: 9e3c1b7a4d2f
Create Date: 2026-05-06 14:30:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a4f6b2c9d1e0"
down_revision = "9e3c1b7a4d2f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "avatar_color",
                sa.String(length=24),
                nullable=False,
                server_default="amber",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("avatar_color")
