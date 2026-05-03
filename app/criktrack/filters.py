"""Jinja template filters used across CRIKTRACK templates.

This module centralises small presentation helpers that format values for
server-rendered templates, such as user initials and human friendly dates.
"""

from __future__ import annotations

from datetime import UTC, datetime

from flask import Flask


def register_filters(app: Flask) -> None:
    """Register all project specific Jinja filters on the Flask app."""
    app.jinja_env.filters["initials"] = initials
    # Deprecated.
    app.jinja_env.filters["relative_time"] = relative_time
    app.jinja_env.filters["pretty_date"] = pretty_date


def initials(name: str | None) -> str:
    """Return a short uppercase initials string derived from a display name."""
    if not name:
        return "??"
    parts = [p for p in name.strip().split() if p]
    if len(parts) == 1:
        return parts[0][:2].upper()
    # Use the first letter of the first and last name parts,
    # which is a common convention for initials.
    return (parts[0][0] + parts[-1][0]).upper()


def relative_time(value: datetime | None) -> str:
    """Format a datetime as a compact relative time string for recent events."""
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
    """Format a date-like object as ``DD Mon YYYY`` for template display."""
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y")
    return value.strftime("%d %b %Y")
