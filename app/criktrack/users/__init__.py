"""Users blueprint: dashboard (organizer/fan), public profile, profile edit."""

from flask import Blueprint

bp = Blueprint("users", __name__)

from . import routes
