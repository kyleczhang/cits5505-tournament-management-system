from __future__ import annotations

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..decorators import require_role
from ..extensions import db
from ..models import (
    Match,
    MatchStatus,
    Team,
    Tournament,
    TournamentFormat,
    TournamentStatus,
    Venue,
)
from ..integrations.geocoding import geocode_address
from . import bp
from .forms import TournamentCreateForm

_PAGE_SIZE = 9


def _team_short_code(name: str, fallback: str = "TBD") -> str:
    cleaned = "".join(c for c in name.upper() if c.isalpha())
    return (cleaned[:3] or fallback)[:4]


@bp.route("")
def list_view():
    q = (request.args.get("q") or "").strip()
    status_arg = (request.args.get("status") or "all").lower()
    page = max(int(request.args.get("page", 1) or 1), 1)

    query = Tournament.query.order_by(Tournament.start_date.desc())
    if q:
        like = f"%{q}%"
        query = query.filter(Tournament.name.ilike(like))
    if status_arg in {"upcoming", "live", "completed"}:
        query = query.filter(Tournament.status == TournamentStatus(status_arg))

    total = query.count()
    tournaments = (
        query.offset((page - 1) * _PAGE_SIZE).limit(_PAGE_SIZE).all()
    )
    pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)

    return render_template(
        "tournaments/list.html",
        tournaments=tournaments,
        q=q,
        status=status_arg,
        page=page,
        pages=pages,
        total=total,
    )


@bp.route("/create", methods=["GET", "POST"])
@login_required
@require_role("organizer")
def create():
    form = TournamentCreateForm()
    team_names_raw = request.form.getlist("team_name") if request.method == "POST" else []
    team_names = [n.strip() for n in team_names_raw if (n or "").strip()]

    if form.validate_on_submit():
        if len(team_names) < 2:
            flash("Add at least two teams to create a tournament.", "warning")
            return render_template(
                "tournaments/create.html", form=form, team_names=team_names_raw
            )

        venue = None
        if form.venue_name.data and form.venue_address.data:
            address = form.venue_address.data.strip()
            coords = geocode_address(address)
            venue = Venue(
                name=form.venue_name.data.strip(),
                address=address,
                lat=coords[0] if coords else None,
                lng=coords[1] if coords else None,
            )
            db.session.add(venue)
            db.session.flush()

        tournament = Tournament(
            name=form.name.data.strip(),
            description=(form.description.data or "").strip() or None,
            format=TournamentFormat(form.format.data),
            status=TournamentStatus.UPCOMING,
            start_date=form.start_date.data,
            team_count=len(team_names),
            organiser_id=current_user.id,
            venue_id=venue.id if venue else None,
        )
        db.session.add(tournament)
        db.session.flush()

        for name in team_names:
            db.session.add(
                Team(
                    tournament_id=tournament.id,
                    name=name,
                    short_code=_team_short_code(name),
                )
            )

        db.session.commit()
        flash("Tournament created. Add fixtures next.", "success")
        return redirect(url_for("tournaments.detail", tournament_id=tournament.id))

    return render_template(
        "tournaments/create.html", form=form, team_names=team_names_raw
    )


def _ordered_teams(tournament: Tournament) -> list[Team]:
    return sorted(
        tournament.teams,
        key=lambda t: (-t.points, -float(t.nrr or 0), t.name),
    )


def _match_payload(matches: list[Match]) -> list[dict]:
    payload = []
    for m in matches:
        innings = {i.batting_team_id: i for i in m.innings}
        a = innings.get(m.team_a_id)
        b = innings.get(m.team_b_id)
        payload.append({
            "match": m,
            "a_score": f"{a.runs}/{a.wickets}" if a else None,
            "b_score": f"{b.runs}/{b.wickets}" if b else None,
        })
    return payload


@bp.route("/<int:tournament_id>")
def detail(tournament_id: int):
    tournament = db.session.get(Tournament, tournament_id) or abort(404)

    matches = (
        Match.query.filter_by(tournament_id=tournament.id)
        .order_by(Match.scheduled_at)
        .all()
    )
    standings = _ordered_teams(tournament)

    return render_template(
        "tournaments/detail.html",
        tournament=tournament,
        teams=standings,
        matches=_match_payload(matches),
        is_organiser=(
            current_user.is_authenticated
            and current_user.id == tournament.organiser_id
        ),
    )


@bp.route("/<slug>/share")
def public(slug: str):
    tournament = (
        Tournament.query.filter_by(share_slug=slug).first() or abort(404)
    )
    standings = _ordered_teams(tournament)
    recent = (
        Match.query.filter_by(
            tournament_id=tournament.id, status=MatchStatus.COMPLETED
        )
        .order_by(Match.scheduled_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "tournaments/public.html",
        tournament=tournament,
        teams=standings,
        recent=_match_payload(recent),
    )
