from flask import Blueprint

bp = Blueprint("comments", __name__)

from . import routes  # noqa: E402,F401