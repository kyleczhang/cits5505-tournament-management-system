"""Auth blueprint: register, login, logout, and the open-redirect guard."""

from flask import Blueprint

bp = Blueprint("auth", __name__)

from . import routes
