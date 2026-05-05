"""Errors blueprint: app-wide 400/401/403/404/500 handlers (HTML or JSON)."""

from flask import Blueprint

bp = Blueprint("errors", __name__)

from . import handlers  # noqa: E402,F401
