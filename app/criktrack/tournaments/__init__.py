"""Tournaments blueprint: list, create, detail, and public share views."""

from flask import Blueprint

bp = Blueprint("tournaments", __name__)

from . import routes
