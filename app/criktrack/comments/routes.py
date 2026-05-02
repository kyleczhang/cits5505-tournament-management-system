from __future__ import annotations

from flask import abort, jsonify, request
from flask_login import current_user

from ..extensions import db
from ..models import Comment, Match, Tournament
from . import bp

_MAX_LEN = 500


def _serialize(rows):
    return jsonify([c.to_dict() for c in rows])


def _ensure_body() -> str:
    if not current_user.is_authenticated:
        abort(401)
    payload = request.get_json(silent=True) or {}
    body = (payload.get("body") or "").strip()
    if not body:
        abort(400, "Comment body is required.")
    if len(body) > _MAX_LEN:
        abort(400, f"Comment too long (max {_MAX_LEN} chars).")
    return body


@bp.route("/matches/<int:match_id>/comments", methods=["GET"])
def list_match(match_id: int):
    db.session.get(Match, match_id) or abort(404)
    rows = (
        Comment.query.filter_by(match_id=match_id)
        .order_by(Comment.created_at.desc())
        .all()
    )
    return _serialize(rows)


@bp.route("/matches/<int:match_id>/comments", methods=["POST"])
def create_match(match_id: int):
    db.session.get(Match, match_id) or abort(404)
    body = _ensure_body()
    comment = Comment(
        match_id=match_id, user_id=current_user.id, body=body
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_dict()), 201


@bp.route("/tournaments/<int:tournament_id>/comments", methods=["GET"])
def list_tournament(tournament_id: int):
    db.session.get(Tournament, tournament_id) or abort(404)
    rows = (
        Comment.query.filter_by(tournament_id=tournament_id)
        .order_by(Comment.created_at.desc())
        .all()
    )
    return _serialize(rows)


@bp.route("/tournaments/<int:tournament_id>/comments", methods=["POST"])
def create_tournament(tournament_id: int):
    db.session.get(Tournament, tournament_id) or abort(404)
    body = _ensure_body()
    comment = Comment(
        tournament_id=tournament_id, user_id=current_user.id, body=body
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_dict()), 201