"""Matches blueprint: scorecard view and organiser-only result recording."""

from flask import Blueprint

bp = Blueprint("matches", __name__)

from . import routes
