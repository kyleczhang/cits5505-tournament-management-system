"""Teams blueprint: organiser-owned team and roster management."""

from flask import Blueprint

bp = Blueprint("teams", __name__)

from . import routes  # noqa: E402,F401
