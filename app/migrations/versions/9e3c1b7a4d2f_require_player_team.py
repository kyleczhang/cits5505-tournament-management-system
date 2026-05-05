"""Require every player to belong to a team.

Revision ID: 9e3c1b7a4d2f
Revises: 6d7a1a0c4f5f
Create Date: 2026-05-05 20:45:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9e3c1b7a4d2f"
down_revision = "6d7a1a0c4f5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("DELETE FROM players WHERE team_id IS NULL"))
    with op.batch_alter_table("players", schema=None) as batch_op:
        batch_op.alter_column(
            "team_id",
            existing_type=sa.Integer(),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("players", schema=None) as batch_op:
        batch_op.alter_column(
            "team_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
