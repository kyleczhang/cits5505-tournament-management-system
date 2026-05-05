"""Follows blueprint: JSON REST API for following tournaments, teams, players."""

from flask import Blueprint

bp = Blueprint("follows", __name__)

from . import routes  # noqa: E402,F401
