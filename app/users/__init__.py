from flask import Blueprint

bp = Blueprint("users", __name__)

from . import routes  # noqa: E402,F401
