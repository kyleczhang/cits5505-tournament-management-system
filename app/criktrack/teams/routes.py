from __future__ import annotations

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..decorators import require_role
from ..extensions import db
from ..models import BattingEntry, BowlingEntry, Player, PlayerRole, Team
from . import bp
from .forms import PlayerForm, TeamForm


def _owned_team_or_404(team_id: int) -> Team:
    team = db.session.get(Team, team_id) or abort(404)
    if team.organiser_id != current_user.id:
        abort(403)
    return team


def _player_for_team_or_404(team: Team, player_id: int) -> Player:
    player = db.session.get(Player, player_id) or abort(404)
    if player.team_id != team.id:
        abort(404)
    return player


def _player_has_scorecard_history(player_id: int) -> bool:
    return (
        BattingEntry.query.filter_by(player_id=player_id).first() is not None
        or BowlingEntry.query.filter_by(player_id=player_id).first() is not None
    )


@bp.route("")
@login_required
@require_role("organizer")
def list_view():
    teams = (
        Team.query.filter_by(organiser_id=current_user.id).order_by(Team.name.asc()).all()
    )
    return render_template("teams/list.html", teams=teams)


@bp.route("/create", methods=["GET", "POST"])
@login_required
@require_role("organizer")
def create():
    form = TeamForm()
    if form.validate_on_submit():
        team = Team(
            organiser_id=current_user.id,
            name=form.name.data.strip(),
            short_code=form.short_code.data.strip().upper(),
        )
        db.session.add(team)
        db.session.commit()
        flash("Team created.", "success")
        return redirect(url_for("teams.detail", team_id=team.id))
    return render_template("teams/form.html", form=form, page_title="Create team")


@bp.route("/<int:team_id>")
@login_required
@require_role("organizer")
def detail(team_id: int):
    team = _owned_team_or_404(team_id)
    player_form = PlayerForm()
    return render_template(
        "teams/detail.html",
        team=team,
        player_form=player_form,
        registrations=len(team.tournament_entries),
    )


@bp.route("/<int:team_id>/edit", methods=["GET", "POST"])
@login_required
@require_role("organizer")
def edit(team_id: int):
    team = _owned_team_or_404(team_id)
    form = TeamForm(obj=team)
    if form.validate_on_submit():
        team.name = form.name.data.strip()
        team.short_code = form.short_code.data.strip().upper()
        db.session.commit()
        flash("Team updated.", "success")
        return redirect(url_for("teams.detail", team_id=team.id))
    return render_template("teams/form.html", form=form, page_title="Edit team")


@bp.route("/<int:team_id>/players/add", methods=["POST"])
@login_required
@require_role("organizer")
def add_player(team_id: int):
    team = _owned_team_or_404(team_id)
    form = PlayerForm()
    if form.validate_on_submit():
        db.session.add(
            Player(
                team_id=team.id,
                name=form.name.data.strip(),
                role=PlayerRole(form.role.data),
            )
        )
        db.session.commit()
        flash("Player added to roster.", "success")
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "warning")
    return redirect(url_for("teams.detail", team_id=team.id))


@bp.route("/<int:team_id>/players/<int:player_id>/edit", methods=["GET", "POST"])
@login_required
@require_role("organizer")
def edit_player(team_id: int, player_id: int):
    team = _owned_team_or_404(team_id)
    player = _player_for_team_or_404(team, player_id)
    form = PlayerForm(obj=player)
    if form.validate_on_submit():
        player.name = form.name.data.strip()
        player.role = PlayerRole(form.role.data)
        db.session.commit()
        flash("Player updated.", "success")
        return redirect(url_for("teams.detail", team_id=team.id))
    return render_template(
        "teams/player_form.html",
        form=form,
        team=team,
        player=player,
        page_title="Edit player",
    )


@bp.route("/<int:team_id>/players/<int:player_id>/delete", methods=["POST"])
@login_required
@require_role("organizer")
def delete_player(team_id: int, player_id: int):
    team = _owned_team_or_404(team_id)
    player = _player_for_team_or_404(team, player_id)
    if _player_has_scorecard_history(player.id):
        flash(
            "This player already appears in recorded scorecards and cannot be removed.",
            "warning",
        )
        return redirect(url_for("teams.detail", team_id=team.id))
    db.session.delete(player)
    db.session.commit()
    flash("Player removed from roster.", "success")
    return redirect(url_for("teams.detail", team_id=team.id))


@bp.route("/<int:team_id>/delete", methods=["POST"])
@login_required
@require_role("organizer")
def delete(team_id: int):
    team = _owned_team_or_404(team_id)
    if team.tournament_entries:
        flash(
            "Remove this team from its tournaments before deleting it.",
            "warning",
        )
        return redirect(url_for("teams.detail", team_id=team.id))

    db.session.delete(team)
    db.session.commit()
    flash("Team deleted.", "success")
    return redirect(url_for("teams.list_view"))
