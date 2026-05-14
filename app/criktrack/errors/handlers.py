"""HTTP error handlers — content-negotiate between rendered templates and JSON."""

from flask import jsonify, render_template

from ..decorators import wants_json
from . import bp


def _respond(code: int, key: str, template: str):
    """Return JSON for API clients (per `wants_json()`), otherwise the HTML error page."""
    if wants_json():
        return jsonify({"error": key}), code
    return render_template(template), code


@bp.app_errorhandler(400)
def bad_request(_err):
    """Return the configured 400 response."""
    return _respond(400, "bad_request", "errors/400.html")


@bp.app_errorhandler(401)
def unauthorized(_err):
    """Return the configured 401 response."""
    return _respond(401, "auth", "errors/401.html")


@bp.app_errorhandler(403)
def forbidden(_err):
    """Return the configured 403 response."""
    return _respond(403, "forbidden", "errors/403.html")


@bp.app_errorhandler(404)
def not_found(_err):
    """Return the configured 404 response."""
    return _respond(404, "not_found", "errors/404.html")


@bp.app_errorhandler(500)
def internal_error(_err):
    """Roll back the session and return the configured 500 response."""
    return _respond(500, "internal", "errors/500.html")
