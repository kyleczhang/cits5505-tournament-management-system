from flask import Blueprint

bp = Blueprint("tournaments", __name__)

from . import routes  # noqa: E402,F401
