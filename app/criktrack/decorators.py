from __future__ import annotations

from functools import wraps

from flask import abort, request
from flask_login import current_user


def require_role(role: str):
    """Restrict a view to users whose Role enum value matches ``role``."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role.value != role:
                abort(403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def wants_json() -> bool:
    """True when the request prefers JSON over HTML."""
    accept = request.accept_mimetypes
    if not accept:
        return request.is_json
    best = accept.best_match(["application/json", "text/html"])
    return best == "application/json"
