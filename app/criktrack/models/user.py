"""User and Role models — authentication identity and authorisation tier."""

from __future__ import annotations

import enum
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db

AVATAR_COLOR_CHOICES = [
    ("amber", "Championship Gold"),
    ("teal", "Pitch Teal"),
    ("violet", "Stadium Violet"),
    ("blue", "Royal Blue"),
    ("crimson", "Boundary Red"),
    ("slate", "Night Slate"),
]
_AVATAR_COLOR_VALUES = {value for value, _ in AVATAR_COLOR_CHOICES}
DEFAULT_AVATAR_COLOR = "amber"


class Role(str, enum.Enum):
    """Authorisation role; ORGANIZER can create/edit tournaments and matches."""

    ORGANIZER = "organizer"
    USER = "user"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class User(db.Model, UserMixin):
    """Application user; integrates with Flask-Login via UserMixin."""

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
    avatar_color = db.Column(
        db.String(24), nullable=False, default=DEFAULT_AVATAR_COLOR
    )
    location = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organised_tournaments = db.relationship(
        "Tournament", back_populates="organiser", lazy="dynamic"
    )
    teams = db.relationship("Team", back_populates="organiser", lazy="dynamic")
    comments = db.relationship("Comment", back_populates="user", lazy="dynamic")
    follows = db.relationship(
        "Follow", back_populates="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    # ---- password helpers -------------------------------------------------
    def set_password(self, password: str) -> None:
        """Hash and store the password using PBKDF2-SHA256 (600k iterations)."""
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256:600000", salt_length=16
        )

    def check_password(self, password: str) -> bool:
        """Return True if the plaintext password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    # ---- presentation helpers --------------------------------------------
    @property
    def initials(self) -> str:
        """Two-letter initials derived from display_name for avatar fallbacks."""
        parts = [p for p in (self.display_name or "").strip().split() if p]
        if not parts:
            return "??"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    @property
    def avatar_color_token(self) -> str:
        """Validated avatar theme token with a safe default for legacy rows."""
        if self.avatar_color in _AVATAR_COLOR_VALUES:
            return self.avatar_color
        return DEFAULT_AVATAR_COLOR

    @property
    def avatar_class(self) -> str:
        """CSS class applied to initials-based avatar badges."""
        return f"avatar-{self.avatar_color_token}"

    def to_dict(self) -> dict:
        """Serialise the user for JSON responses (camelCase keys for the JS client)."""
        return {
            "id": self.id,
            "displayName": self.display_name,
            "initials": self.initials,
            "email": self.email,
            "role": self.role.value,
            "bio": self.bio,
            "avatarUrl": self.avatar_url,
            "avatarColor": self.avatar_color_token,
            "avatarColorClass": self.avatar_class,
            "location": self.location,
        }
