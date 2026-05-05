"""Live blueprint: thin proxy over the cricketdata.org live-matches feed."""

from flask import Blueprint

bp = Blueprint("live", __name__)

from . import routes  # noqa: E402,F401
