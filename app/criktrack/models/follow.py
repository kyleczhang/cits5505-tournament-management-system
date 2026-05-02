from __future__ import annotations

import enum
from datetime import datetime

from ..extensions import db


class FollowTarget(str, enum.Enum):
    TOURNAMENT = "tournament"
    TEAM = "team"
    PLAYER = "player"


class Follow(db.Model):
    __tablename__ = "follows"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    target_type = db.Column(
        db.Enum(FollowTarget, values_callable=lambda x: [m.value for m in x]),
        nullable=False,
    )
    target_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="follows")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "target_type", "target_id", name="uq_follow_user_target"
        ),
        db.Index("ix_follows_target", "target_type", "target_id"),
    )
