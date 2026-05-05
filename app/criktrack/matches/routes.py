"""Match routes: scorecards, organiser match scheduling, and result recording."""

from __future__ import annotations

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..decorators import require_role
from ..extensions import db
from ..models import Match, MatchStatus, Player, Team, Tournament
from . import bp
from .forms import MatchCreateForm
from .services import ValidationError, save_result, validate_payload


def _load(tournament_id: int, match_id: int) -> tuple[Tournament, Match]:
    """Fetch tournament+match, 404ing if either is missing or the match is foreign."""
    tournament = db.session.get(Tournament, tournament_id) or abort(404)
    match = db.session.get(Match, match_id) or abort(404)
    if match.tournament_id != tournament.id:
        # Guard against URL tampering: a match must belong to the tournament in the URL.
        abort(404)
    return tournament, match


def _owned_tournament_or_403(tournament_id: int) -> Tournament:
    tournament = db.session.get(Tournament, tournament_id) or abort(404)
    if tournament.organiser_id != current_user.id:
        abort(403)
    return tournament


def _registered_teams(tournament: Tournament) -> list[Team]:
    return [entry.team for entry in tournament.tournament_teams]


def _team_rosters(match: Match) -> dict[int, list[Player]]:
    return {
        match.team_a_id: sorted(match.team_a.players, key=lambda player: player.name),
        match.team_b_id: sorted(match.team_b.players, key=lambda player: player.name),
    }


@bp.route("/tournaments/<int:tournament_id>/matches/<int:match_id>")
def scorecard(tournament_id: int, match_id: int):
    tournament, match = _load(tournament_id, match_id)
    is_organiser = (
        current_user.is_authenticated and current_user.id == tournament.organiser_id
    )
    return render_template(
        "matches/scorecard.html",
        tournament=tournament,
        match=match,
        is_organiser=is_organiser,
    )


@bp.route("/tournaments/<int:tournament_id>/matches/create", methods=["GET", "POST"])
@login_required
@require_role("organizer")
def create(tournament_id: int):
    tournament = _owned_tournament_or_403(tournament_id)
    teams = _registered_teams(tournament)
    if len(teams) < 2:
        flash("Add at least two teams to the tournament before scheduling matches.", "warning")
        return redirect(url_for("tournaments.detail", tournament_id=tournament.id))

    form = MatchCreateForm()
    choices = [(team.id, team.name) for team in teams]
    form.team_a_id.choices = choices
    form.team_b_id.choices = choices

    if form.validate_on_submit():
        if form.team_a_id.data == form.team_b_id.data:
            form.team_b_id.errors.append("Team B must be different from Team A.")
            return render_template("matches/create.html", tournament=tournament, form=form)

        match = Match(
            tournament_id=tournament.id,
            team_a_id=form.team_a_id.data,
            team_b_id=form.team_b_id.data,
            scheduled_at=form.scheduled_at.data,
            status=MatchStatus.UPCOMING,
            venue_id=tournament.venue_id,
        )
        db.session.add(match)
        db.session.commit()
        flash("Match scheduled.", "success")
        return redirect(url_for("tournaments.detail", tournament_id=tournament.id))

    return render_template("matches/create.html", tournament=tournament, form=form)


@bp.route(
    "/tournaments/<int:tournament_id>/matches/<int:match_id>/record",
    methods=["GET", "POST"],
)
@login_required
@require_role("organizer")
def record(tournament_id: int, match_id: int):
    tournament, match = _load(tournament_id, match_id)
    # Ownership check: the organizer role alone isn't enough — only the tournament's
    # own organiser may record results for its matches.
    if tournament.organiser_id != current_user.id:
        abort(403)

    if request.method == "POST":
        if not request.is_json:
            return jsonify({"errors": {"_": "Expected application/json."}}), 400
        try:
            normalised = validate_payload(request.get_json(silent=True) or {}, match)
        except ValidationError as exc:
            return jsonify({"errors": exc.errors}), 400
        # Always go through save_result — it owns the wipe-and-rebuild + standings
        # recompute. Mutating match.status/winner_id directly would drift standings.
        save_result(match, normalised)
        return jsonify(
            {
                "ok": True,
                "redirect": url_for(
                    "matches.scorecard",
                    tournament_id=tournament.id,
                    match_id=match.id,
                ),
            }
        )

    return render_template(
        "matches/record.html",
        tournament=tournament,
        match=match,
        team_rosters=_team_rosters(match),
        roster_payload={
            str(team_id): [{"id": player.id, "name": player.name} for player in players]
            for team_id, players in _team_rosters(match).items()
        },
    )
