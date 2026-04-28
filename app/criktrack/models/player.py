from __future__ import annotations

import enum

from ..extensions import db


class PlayerRole(str, enum.Enum):
    BATTER = "batter"
    BOWLER = "bowler"
    ALL_ROUNDER = "all_rounder"
    WICKET_KEEPER = "wicket_keeper"


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=True)
    name = db.Column(db.String(80), nullable=False)
    role = db.Column(
        db.Enum(PlayerRole, values_callable=lambda x: [m.value for m in x]),
        nullable=False,
        default=PlayerRole.ALL_ROUNDER,
    )

    team = db.relationship("Team", back_populates="players")
