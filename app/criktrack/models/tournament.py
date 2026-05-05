"""Tournament and Team models — the top-level competition entity and its participants."""

from __future__ import annotations

import enum
import secrets
from datetime import datetime

from ..extensions import db


class TournamentFormat(str, enum.Enum):
    ROUND_ROBIN = "round_robin"
    KNOCKOUT = "knockout"
    GROUP_STAGE = "group_stage"


class TournamentStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    LIVE = "live"
    COMPLETED = "completed"


def _generate_share_slug() -> str:
    """Random URL-safe slug for the public anonymous share view."""
    return secrets.token_urlsafe(9)  # ~12 chars, URL-safe


class Tournament(db.Model):
    """A cricket tournament organised by one user, containing teams and matches."""

    __tablename__ = "tournaments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    format = db.Column(
        db.Enum(TournamentFormat, values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=TournamentFormat.ROUND_ROBIN,
    )
    status = db.Column(
        db.Enum(TournamentStatus, values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=TournamentStatus.UPCOMING,
        index=True,
    )
    start_date = db.Column(db.Date, nullable=False)
    team_count = db.Column(db.Integer, nullable=False, default=0)
    organiser_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"), nullable=True)
    # Used by the public /tournaments/p/<slug> view; unguessable so it acts as a capability token.
    share_slug = db.Column(
        db.String(32),
        unique=True,
        nullable=False,
        default=_generate_share_slug,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organiser = db.relationship("User", back_populates="organised_tournaments")
    venue = db.relationship("Venue", lazy="joined")
    teams = db.relationship(
        "Team", back_populates="tournament", cascade="all, delete-orphan"
    )
    matches = db.relationship(
        "Match", back_populates="tournament", cascade="all, delete-orphan"
    )
    comments = db.relationship(
        "Comment", back_populates="tournament", cascade="all, delete-orphan"
    )

    def to_summary_dict(self) -> dict:
        """Compact JSON view used in tournament listings and the share page."""
        return {
            "id": self.id,
            "name": self.name,
            "format": self.format.value,
            "status": self.status.value,
            "teams": self.team_count,
            "startDate": self.start_date.isoformat() if self.start_date else None,
            "organiser": self.organiser.display_name if self.organiser else None,
            "shareSlug": self.share_slug,
        }


class Team(db.Model):
    """A team competing in a single tournament; standings columns are derived state."""

    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(
        db.Integer, db.ForeignKey("tournaments.id"), nullable=False, index=True
    )
    name = db.Column(db.String(80), nullable=False)
    short_code = db.Column(db.String(4), nullable=False, default="???")

    # Denormalised standings columns; recomputed by services.
    played = db.Column(db.Integer, nullable=False, default=0)
    won = db.Column(db.Integer, nullable=False, default=0)
    lost = db.Column(db.Integer, nullable=False, default=0)
    points = db.Column(db.Integer, nullable=False, default=0)
    nrr = db.Column(db.Numeric(5, 2), nullable=False, default=0)

    tournament = db.relationship("Tournament", back_populates="teams")
    players = db.relationship(
        "Player", back_populates="team", cascade="all, delete-orphan"
    )
