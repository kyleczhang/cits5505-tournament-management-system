from flask import Blueprint

bp = Blueprint("players", __name__)

from . import routes  # noqa: E402,F401
