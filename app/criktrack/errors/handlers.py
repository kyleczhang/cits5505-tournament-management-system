from flask import jsonify, render_template

from ..decorators import wants_json
from . import bp


def _respond(code: int, key: str, template: str):
    if wants_json():
        return jsonify({"error": key}), code
    return render_template(template), code


@bp.app_errorhandler(400)
def bad_request(_err):
    return _respond(400, "bad_request", "errors/400.html")


@bp.app_errorhandler(401)
def unauthorized(_err):
    return _respond(401, "auth", "errors/401.html")


@bp.app_errorhandler(403)
def forbidden(_err):
    return _respond(403, "forbidden", "errors/403.html")


@bp.app_errorhandler(404)
def not_found(_err):
    return _respond(404, "not_found", "errors/404.html")


@bp.app_errorhandler(500)
def internal_error(_err):
    return _respond(500, "internal", "errors/500.html")
