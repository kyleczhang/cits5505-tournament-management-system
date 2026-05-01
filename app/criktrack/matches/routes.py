from __future__ import annotations

from flask import abort, jsonify, render_template, request, url_for
from flask_login import current_user, login_required

from ..decorators import require_role
from ..extensions import db
from ..models import Match, Tournament
from . import bp
from .services import ValidationError, save_result, validate_payload


def _load(tournament_id: int, match_id: int) -> tuple[Tournament, Match]:
    tournament = db.session.get(Tournament, tournament_id) or abort(404)
    match = db.session.get(Match, match_id) or abort(404)
    if match.tournament_id != tournament.id:
        abort(404)
    return tournament, match


@bp.route("/tournaments/<int:tournament_id>/matches/<int:match_id>")
def scorecard(tournament_id: int, match_id: int):
    tournament, match = _load(tournament_id, match_id)
    is_organiser = (
        current_user.is_authenticated
        and current_user.id == tournament.organiser_id
    )
    return render_template(
        "matches/scorecard.html",
        tournament=tournament,
        match=match,
        is_organiser=is_organiser,
    )


@bp.route(
    "/tournaments/<int:tournament_id>/matches/<int:match_id>/record",
    methods=["GET", "POST"],
)
@login_required
@require_role("organizer")
def record(tournament_id: int, match_id: int):
    tournament, match = _load(tournament_id, match_id)
    if tournament.organiser_id != current_user.id:
        abort(403)

    if request.method == "POST":
        if not request.is_json:
            return jsonify({"errors": {"_": "Expected application/json."}}), 400
        try:
            normalised = validate_payload(request.get_json(silent=True) or {}, match)
        except ValidationError as exc:
            return jsonify({"errors": exc.errors}), 400
        save_result(match, normalised)
        return jsonify({
            "ok": True,
            "redirect": url_for(
                "matches.scorecard",
                tournament_id=tournament.id,
                match_id=match.id,
            ),
        })

    return render_template(
        "matches/record.html",
        tournament=tournament,
        match=match,
    )
