from __future__ import annotations

from datetime import UTC, datetime

from ..extensions import db


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(
        db.Integer, db.ForeignKey("matches.id"), nullable=True, index=True
    )
    tournament_id = db.Column(
        db.Integer, db.ForeignKey("tournaments.id"), nullable=True, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    match = db.relationship("Match", back_populates="comments")
    tournament = db.relationship("Tournament", back_populates="comments")
    user = db.relationship("User", back_populates="comments")

    __table_args__ = (
        db.CheckConstraint(
            "(match_id IS NOT NULL) <> (tournament_id IS NOT NULL)",
            name="ck_comment_target_xor",
        ),
    )

    def to_dict(self) -> dict:
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        author = self.user
        return {
            "id": self.id,
            "matchId": self.match_id,
            "tournamentId": self.tournament_id,
            "authorId": author.id if author else None,
            "authorName": author.display_name if author else "Unknown",
            "initials": author.initials if author else "??",
            "role": author.role.value if author else "user",
            "body": self.body,
            "createdAt": created.isoformat(),
        }
