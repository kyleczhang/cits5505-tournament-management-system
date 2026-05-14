"""Team domain models — reusable teams and tournament-specific participation rows."""

from __future__ import annotations

from ..extensions import db


class Team(db.Model):
    """A reusable team owned by one organiser and available across tournaments."""

    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    organiser_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    name = db.Column(db.String(80), nullable=False)
    short_code = db.Column(db.String(4), nullable=False, default="???")

    organiser = db.relationship("User", back_populates="teams")
    players = db.relationship(
        "Player", back_populates="team", cascade="all, delete-orphan"
    )
    tournament_entries = db.relationship(
        "TournamentTeam", back_populates="team", cascade="all, delete-orphan"
    )


class TournamentTeam(db.Model):
    """A team's registration in a tournament, including tournament-scoped standings."""

    __tablename__ = "tournament_teams"

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(
        db.Integer, db.ForeignKey("tournaments.id"), nullable=False, index=True
    )
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False, index=True)

    played = db.Column(db.Integer, nullable=False, default=0)
    won = db.Column(db.Integer, nullable=False, default=0)
    lost = db.Column(db.Integer, nullable=False, default=0)
    points = db.Column(db.Integer, nullable=False, default=0)
    nrr = db.Column(db.Numeric(5, 2), nullable=False, default=0)

    tournament = db.relationship("Tournament", back_populates="tournament_teams")
    team = db.relationship("Team", back_populates="tournament_entries")

    __table_args__ = (
        db.UniqueConstraint("tournament_id", "team_id", name="uq_tournament_team"),
    )

    @property
    def name(self) -> str:
        """Return the registered team name for this tournament entry."""
        return self.team.name

    @property
    def short_code(self) -> str:
        """Return the registered team short code for this tournament entry."""
        return self.team.short_code
