from __future__ import annotations

import enum
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class Role(str, enum.Enum):
    ORGANIZER = "organizer"
    USER = "user"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum(Role, values_callable=lambda x: [m.value for m in x]),
        default=Role.USER,
        nullable=False,
    )
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organised_tournaments = db.relationship(
        "Tournament", back_populates="organiser", lazy="dynamic"
    )
    comments = db.relationship("Comment", back_populates="user", lazy="dynamic")
    follows = db.relationship(
        "Follow", back_populates="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    # ---- password helpers -------------------------------------------------
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256:600000", salt_length=16
        )

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # ---- presentation helpers --------------------------------------------
    @property
    def initials(self) -> str:
        parts = [p for p in (self.display_name or "").strip().split() if p]
        if not parts:
            return "??"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "displayName": self.display_name,
            "initials": self.initials,
            "email": self.email,
            "role": self.role.value,
            "bio": self.bio,
            "avatarUrl": self.avatar_url,
            "location": self.location,
        }
