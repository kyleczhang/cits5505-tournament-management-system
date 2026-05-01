from __future__ import annotations

from flask import abort, jsonify, request
from flask_login import current_user

from ..extensions import db
from ..models import Follow, FollowTarget, Player, Team, Tournament
from . import bp

_TARGET_MODELS = {
    FollowTarget.TOURNAMENT: Tournament,
    FollowTarget.TEAM: Team,
    FollowTarget.PLAYER: Player,
}


def _require_auth() -> None:
    if not current_user.is_authenticated:
        abort(401)


def _parse_target() -> tuple[FollowTarget, int]:
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
    _require_auth()
    target_type, target_id = _parse_target()
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
    _require_auth()
    target_type, target_id = _parse_target()
    Follow.query.filter_by(
        user_id=current_user.id, target_type=target_type, target_id=target_id
    ).delete()
    db.session.commit()
    return jsonify({"following": False}), 200


@bp.route("/follow/status", methods=["GET"])
def status():
    _require_auth()
    raw_type = (request.args.get("targetType") or "").strip().lower()
    raw_id = request.args.get("targetId")
    try:
        target_type = FollowTarget(raw_type)
        target_id = int(raw_id)
    except (TypeError, ValueError):
        abort(400)
    exists = Follow.query.filter_by(
        user_id=current_user.id, target_type=target_type, target_id=target_id
    ).first() is not None
    return jsonify({"following": exists})
