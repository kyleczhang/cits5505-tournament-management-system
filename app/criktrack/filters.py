from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask


def register_filters(app: Flask) -> None:
    app.jinja_env.filters["initials"] = initials
    app.jinja_env.filters["relative_time"] = relative_time
    app.jinja_env.filters["pretty_date"] = pretty_date


def initials(name: str | None) -> str:
    if not name:
        return "??"
    parts = [p for p in name.strip().split() if p]
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def relative_time(value: datetime | None) -> str:
    if not value:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    delta = datetime.now(UTC) - value
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{seconds // 60} min ago"
    if seconds < 86400:
        return f"{seconds // 3600} h ago"
    if seconds < 604800:
        return f"{seconds // 86400} d ago"
    return value.strftime("%d %b %Y")


def pretty_date(value) -> str:
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y")
    return value.strftime("%d %b %Y")
