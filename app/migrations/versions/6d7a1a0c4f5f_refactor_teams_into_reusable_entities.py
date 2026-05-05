"""refactor teams into reusable entities

Revision ID: 6d7a1a0c4f5f
Revises: 12128c51cf58
Create Date: 2026-05-05 15:10:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6d7a1a0c4f5f"
down_revision = "12128c51cf58"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tournament_teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("played", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("won", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lost", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("nrr", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournaments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tournament_id", "team_id", name="uq_tournament_team"),
    )
    with op.batch_alter_table("tournament_teams", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_tournament_teams_team_id"), ["team_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_tournament_teams_tournament_id"),
            ["tournament_id"],
            unique=False,
        )

    op.execute(
        sa.text(
            """
            INSERT INTO tournament_teams (tournament_id, team_id, played, won, lost, points, nrr)
            SELECT tournament_id, id, played, won, lost, points, nrr
            FROM teams
            """
        )
    )

    with op.batch_alter_table("teams", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organiser_id", sa.Integer(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE teams
            SET organiser_id = (
                SELECT tournaments.organiser_id
                FROM tournaments
                WHERE tournaments.id = teams.tournament_id
            )
            """
        )
    )

    with op.batch_alter_table("teams", schema=None) as batch_op:
        batch_op.alter_column("organiser_id", nullable=False)
        batch_op.create_foreign_key(
            "fk_teams_organiser_id_users", "users", ["organiser_id"], ["id"]
        )
        batch_op.create_index(batch_op.f("ix_teams_organiser_id"), ["organiser_id"], unique=False)
        batch_op.drop_index(batch_op.f("ix_teams_tournament_id"))
        batch_op.drop_column("tournament_id")
        batch_op.drop_column("played")
        batch_op.drop_column("won")
        batch_op.drop_column("lost")
        batch_op.drop_column("points")
        batch_op.drop_column("nrr")


def downgrade():
    with op.batch_alter_table("teams", schema=None) as batch_op:
        batch_op.add_column(sa.Column("nrr", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("points", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("lost", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("won", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("played", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("tournament_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_teams_tournament_id"), ["tournament_id"], unique=False)

    op.execute(
        sa.text(
            """
            UPDATE teams
            SET tournament_id = (
                SELECT tournament_teams.tournament_id
                FROM tournament_teams
                WHERE tournament_teams.team_id = teams.id
                ORDER BY tournament_teams.tournament_id
                LIMIT 1
            ),
            played = COALESCE((
                SELECT tournament_teams.played
                FROM tournament_teams
                WHERE tournament_teams.team_id = teams.id
                ORDER BY tournament_teams.tournament_id
                LIMIT 1
            ), 0),
            won = COALESCE((
                SELECT tournament_teams.won
                FROM tournament_teams
                WHERE tournament_teams.team_id = teams.id
                ORDER BY tournament_teams.tournament_id
                LIMIT 1
            ), 0),
            lost = COALESCE((
                SELECT tournament_teams.lost
                FROM tournament_teams
                WHERE tournament_teams.team_id = teams.id
                ORDER BY tournament_teams.tournament_id
                LIMIT 1
            ), 0),
            points = COALESCE((
                SELECT tournament_teams.points
                FROM tournament_teams
                WHERE tournament_teams.team_id = teams.id
                ORDER BY tournament_teams.tournament_id
                LIMIT 1
            ), 0),
            nrr = COALESCE((
                SELECT tournament_teams.nrr
                FROM tournament_teams
                WHERE tournament_teams.team_id = teams.id
                ORDER BY tournament_teams.tournament_id
                LIMIT 1
            ), 0)
            """
        )
    )

    with op.batch_alter_table("teams", schema=None) as batch_op:
        batch_op.alter_column("tournament_id", nullable=False)
        batch_op.create_foreign_key(
            "fk_teams_tournament_id_tournaments",
            "tournaments",
            ["tournament_id"],
            ["id"],
        )
        batch_op.drop_index(batch_op.f("ix_teams_organiser_id"))
        batch_op.drop_constraint("fk_teams_organiser_id_users", type_="foreignkey")
        batch_op.drop_column("organiser_id")

    with op.batch_alter_table("tournament_teams", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_tournament_teams_tournament_id"))
        batch_op.drop_index(batch_op.f("ix_tournament_teams_team_id"))

    op.drop_table("tournament_teams")
