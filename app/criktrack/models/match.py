from __future__ import annotations

import enum
from datetime import datetime

from ..extensions import db


class MatchStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    LIVE = "live"
    COMPLETED = "completed"


class TossDecision(str, enum.Enum):
    BAT = "bat"
    BOWL = "bowl"


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(
        db.Integer, db.ForeignKey("tournaments.id"), nullable=False, index=True
    )
    venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"), nullable=True)
    team_a_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    team_b_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(
        db.Enum(MatchStatus, values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=MatchStatus.UPCOMING,
    )
    toss_winner_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    toss_decision = db.Column(
        db.Enum(TossDecision, values_callable=lambda x: [m.value for m in x]),
        nullable=True,
    )
    winner_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    result_text = db.Column(db.String(160), nullable=True)
    external_id = db.Column(db.String(64), nullable=True)

    tournament = db.relationship("Tournament", back_populates="matches")
    venue = db.relationship("Venue")
    team_a = db.relationship("Team", foreign_keys=[team_a_id])
    team_b = db.relationship("Team", foreign_keys=[team_b_id])
    toss_winner = db.relationship("Team", foreign_keys=[toss_winner_id])
    winner = db.relationship("Team", foreign_keys=[winner_id])
    innings = db.relationship(
        "Innings",
        back_populates="match",
        cascade="all, delete-orphan",
        order_by="Innings.inning_number",
    )
    comments = db.relationship(
        "Comment", back_populates="match", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.Index("ix_matches_tournament_scheduled", "tournament_id", "scheduled_at"),
    )


class Innings(db.Model):
    __tablename__ = "innings"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(
        db.Integer, db.ForeignKey("matches.id"), nullable=False, index=True
    )
    inning_number = db.Column(db.Integer, nullable=False, default=1)
    batting_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    bowling_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    runs = db.Column(db.Integer, nullable=False, default=0)
    wickets = db.Column(db.Integer, nullable=False, default=0)
    overs = db.Column(db.Numeric(4, 1), nullable=False, default=0)

    match = db.relationship("Match", back_populates="innings")
    batting_team = db.relationship("Team", foreign_keys=[batting_team_id])
    bowling_team = db.relationship("Team", foreign_keys=[bowling_team_id])
    batting_entries = db.relationship(
        "BattingEntry", back_populates="innings", cascade="all, delete-orphan"
    )
    bowling_entries = db.relationship(
        "BowlingEntry", back_populates="innings", cascade="all, delete-orphan"
    )


class BattingEntry(db.Model):
    __tablename__ = "batting_entries"

    id = db.Column(db.Integer, primary_key=True)
    innings_id = db.Column(
        db.Integer, db.ForeignKey("innings.id"), nullable=False, index=True
    )
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    runs = db.Column(db.Integer, nullable=False, default=0)
    balls = db.Column(db.Integer, nullable=False, default=0)
    fours = db.Column(db.Integer, nullable=False, default=0)
    sixes = db.Column(db.Integer, nullable=False, default=0)
    dismissal = db.Column(db.String(160), nullable=True)
    is_not_out = db.Column(db.Boolean, nullable=False, default=False)

    innings = db.relationship("Innings", back_populates="batting_entries")
    player = db.relationship("Player")

    @property
    def strike_rate(self) -> float:
        return round((self.runs / self.balls) * 100, 1) if self.balls else 0.0


class BowlingEntry(db.Model):
    __tablename__ = "bowling_entries"

    id = db.Column(db.Integer, primary_key=True)
    innings_id = db.Column(
        db.Integer, db.ForeignKey("innings.id"), nullable=False, index=True
    )
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    overs = db.Column(db.Numeric(4, 1), nullable=False, default=0)
    maidens = db.Column(db.Integer, nullable=False, default=0)
    runs = db.Column(db.Integer, nullable=False, default=0)
    wickets = db.Column(db.Integer, nullable=False, default=0)

    innings = db.relationship("Innings", back_populates="bowling_entries")
    player = db.relationship("Player")

    @property
    def economy(self) -> float:
        overs = float(self.overs or 0)
        return round(self.runs / overs, 2) if overs else 0.0
