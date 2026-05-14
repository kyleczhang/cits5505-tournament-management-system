"""JSON endpoints for follow/unfollow and follow status.

POST/DELETE handlers require the ``X-CSRFToken`` header from the front-end.
"""

from __future__ import annotations

from flask import abort, jsonify, request
from flask_login import current_user

from ..extensions import db
from ..models import Follow, FollowTarget, Player, Team, Tournament
from . import bp

# Maps the FollowTarget enum to its concrete model so we can validate that
# the referenced row actually exists before persisting a Follow.
_TARGET_MODELS = {
    FollowTarget.TOURNAMENT: Tournament,
    FollowTarget.TEAM: Team,
    FollowTarget.PLAYER: Player,
}


def _require_auth() -> None:
    """Abort if the current request is unauthenticated."""
    if not current_user.is_authenticated:
        abort(401)


def _parse_target() -> tuple[FollowTarget, int]:
    """Extract and validate ``targetType``/``targetId`` from the JSON body.

    Aborts 400 on bad input and 404 if the referenced row does not exist.
    """
    payload = request.get_json(silent=True) or {}
    raw_type = (payload.get("targetType") or "").strip().lower()
    raw_id = payload.get("targetId")
    try:
        target_type = FollowTarget(raw_type)
    except ValueError:
        abort(400, "Unknown target type.")
    try:
        target_id = int(raw_id)
    except (TypeError, ValueError):
        abort(400, "Invalid target id.")
    if db.session.get(_TARGET_MODELS[target_type], target_id) is None:
        abort(404)
    return target_type, target_id


@bp.route("/follow", methods=["POST"])
def create():
    """Create a follow relationship for the requested target."""
    _require_auth()
    target_type, target_id = _parse_target()
    # Idempotent: a duplicate POST is a no-op rather than a 409 so the UI
    # can safely retry on flaky networks.
    existing = Follow.query.filter_by(
        user_id=current_user.id, target_type=target_type, target_id=target_id
    ).first()
    if existing is None:
        db.session.add(
            Follow(
                user_id=current_user.id,
                target_type=target_type,
                target_id=target_id,
            )
        )
        db.session.commit()
    return jsonify({"following": True}), 200


@bp.route("/follow", methods=["DELETE"])
def delete():
    """Remove a follow relationship for the requested target."""
    _require_auth()
    target_type, target_id = _parse_target()
    Follow.query.filter_by(
        user_id=current_user.id, target_type=target_type, target_id=target_id
    ).delete()
    db.session.commit()
    return jsonify({"following": False}), 200


@bp.route("/follow/status", methods=["GET"])
def status():
    """Return whether the current user follows the requested target."""
    _require_auth()
    raw_type = (request.args.get("targetType") or "").strip().lower()
    raw_id = request.args.get("targetId")
    try:
        target_type = FollowTarget(raw_type)
        target_id = int(raw_id)
    except (TypeError, ValueError):
        abort(400)
    exists = (
        Follow.query.filter_by(
            user_id=current_user.id, target_type=target_type, target_id=target_id
        ).first()
        is not None
    )
    return jsonify({"following": exists})
