from __future__ import annotations

from functools import wraps

from flask import abort, request
from flask_login import current_user


def require_role(role: str):
    """Return a view decorator that enforces a specific authenticated role.

    This is used on Flask view functions that should only be reachable by
    users whose ``current_user.role.value`` matches ``role`` exactly. In this
    project the main use case is organiser-only routes, such as tournament
    creation and match result recording.

    If the request has no authenticated user, the wrapper aborts with ``401``.
    If the user is logged in but has the wrong role, it aborts with ``403``.
    Otherwise it calls the original view unchanged.
    """

    def decorator(fn):
        # ``fn`` is the original Flask view being wrapped, such as ``create``.
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                # Current user is not logged in at all.
                abort(401)
            if current_user.role.value != role:
                # Current user is logged in but does not have the required role.
                abort(403)
            # If we get here, the user is authenticated and has the required role,
            # so call the original view function.
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def wants_json() -> bool:
    """Return whether the current request prefers a JSON response.

    This helper is mainly used by the global error handlers so the app can
    return JSON to API-style callers and HTML templates to browser page
    requests. It first inspects the request ``Accept`` header via Flask's MIME
    negotiation support, choosing between ``application/json`` and
    ``text/html``. If no meaningful ``Accept`` preference is available, it
    falls back to ``request.is_json`` as a practical signal that the client is
    interacting with the app as a JSON endpoint.
    """

    accept = request.accept_mimetypes
    if not accept:
        return request.is_json
    best = accept.best_match(["application/json", "text/html"])
    return best == "application/json"
