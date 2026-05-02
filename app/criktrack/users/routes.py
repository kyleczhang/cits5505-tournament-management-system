from __future__ import annotations

from datetime import date

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ..extensions import db
from ..follows.services import followed_ids
from ..models import (
    Comment,
    FollowTarget,
    Match,
    MatchStatus,
    Player,
    Role,
    Team,
    Tournament,
    TournamentStatus,
    User,
)
from . import bp
from .forms import ProfileEditForm


@bp.route("/dashboard")
@login_required
def dashboard():
    is_organizer = current_user.role == Role.ORGANIZER
    fan_view = request.args.get("as") == "fan"

    if is_organizer and not fan_view:
        return _render_organizer_dashboard()
    return _render_fan_dashboard(viewing_as_fan=is_organizer and fan_view)


def _render_organizer_dashboard():
    organised = (
        Tournament.query.filter_by(organiser_id=current_user.id)
        .order_by(Tournament.start_date.desc())
        .all()
    )
    organised_ids = [t.id for t in organised]

    upcoming_matches = (
        Match.query.filter(
            Match.tournament_id.in_(organised_ids) if organised_ids else False,
            Match.status.in_([MatchStatus.UPCOMING, MatchStatus.LIVE]),
        )
        .order_by(Match.scheduled_at)
        .limit(5)
        .all()
    )
    recent_results = (
        Match.query.filter(
            Match.tournament_id.in_(organised_ids) if organised_ids else False,
            Match.status == MatchStatus.COMPLETED,
        )
        .order_by(Match.scheduled_at.desc())
        .limit(5)
        .all()
    )

    needs_attention = _build_needs_attention(organised, organised_ids)

    summary = {
        "my_tournaments": len(organised),
        "upcoming_matches": len(upcoming_matches),
        "recent_results": len(recent_results),
        "total_players": sum(len(team.players) for t in organised for team in t.teams),
    }

    return render_template(
        "dashboard_organizer.html",
        organised=organised,
        upcoming_matches=upcoming_matches,
        recent_results=recent_results,
        needs_attention=needs_attention,
        summary=summary,
    )


def _build_needs_attention(organised, organised_ids):
    items: list[dict] = []

    live_matches = (
        Match.query.filter(
            Match.tournament_id.in_(organised_ids) if organised_ids else False,
            Match.status == MatchStatus.LIVE,
        )
        .order_by(Match.scheduled_at)
        .all()
    )
    for m in live_matches:
        items.append(
            {
                "kind": "record",
                "label": f"{m.team_a.name} vs {m.team_b.name} is live",
                "hint": f"{m.tournament.name} • record the result",
                "url": url_for(
                    "matches.record",
                    tournament_id=m.tournament_id,
                    match_id=m.id,
                ),
                "cta": "Record now",
            }
        )

    match_counts = {}
    if organised_ids:
        rows = (
            db.session.query(Match.tournament_id, func.count(Match.id))
            .filter(Match.tournament_id.in_(organised_ids))
            .group_by(Match.tournament_id)
            .all()
        )
        match_counts = {tid: c for tid, c in rows}

    for t in organised:
        if t.status == TournamentStatus.COMPLETED:
            continue
        if t.team_count == 0:
            items.append(
                {
                    "kind": "setup",
                    "label": f"{t.name} has no teams yet",
                    "hint": "Add teams before scheduling matches",
                    "url": url_for("tournaments.detail", tournament_id=t.id),
                    "cta": "Add teams",
                }
            )
        elif match_counts.get(t.id, 0) == 0:
            items.append(
                {
                    "kind": "schedule",
                    "label": f"{t.name} has no fixtures",
                    "hint": "Schedule the opening matches",
                    "url": url_for("tournaments.detail", tournament_id=t.id),
                    "cta": "Schedule",
                }
            )

    return items[:6]


def _render_fan_dashboard(viewing_as_fan: bool):
    today = date.today()

    ongoing_tournaments = (
        Tournament.query.filter(Tournament.status == TournamentStatus.LIVE)
        .order_by(Tournament.start_date.desc())
        .limit(6)
        .all()
    )
    upcoming_tournaments = (
        Tournament.query.filter(
            Tournament.status == TournamentStatus.UPCOMING,
            Tournament.start_date >= today,
        )
        .order_by(Tournament.start_date.asc())
        .limit(4)
        .all()
    )
    if not ongoing_tournaments and not upcoming_tournaments:
        ongoing_tournaments = (
            Tournament.query.order_by(Tournament.start_date.desc()).limit(4).all()
        )

    recent_results = (
        Match.query.filter(Match.status == MatchStatus.COMPLETED)
        .order_by(Match.scheduled_at.desc())
        .limit(6)
        .all()
    )

    conversations = _build_conversations()
    following = _build_following()
    profile_completion = _profile_completion(current_user)

    return render_template(
        "dashboard_user.html",
        ongoing_tournaments=ongoing_tournaments,
        upcoming_tournaments=upcoming_tournaments,
        recent_results=recent_results,
        conversations=conversations,
        following=following,
        profile_completion=profile_completion,
        viewing_as_fan=viewing_as_fan,
    )


def _build_following():
    t_ids = followed_ids(FollowTarget.TOURNAMENT)
    team_ids = followed_ids(FollowTarget.TEAM)
    player_ids = followed_ids(FollowTarget.PLAYER)

    tournaments = []
    if t_ids:
        rows = (
            Tournament.query.filter(Tournament.id.in_(t_ids))
            .order_by(Tournament.start_date.desc())
            .limit(6)
            .all()
        )
        last_matches = _latest_match_per_tournament([r.id for r in rows])
        tournaments = [
            {"tournament": t, "latest": last_matches.get(t.id)} for t in rows
        ]

    teams = []
    if team_ids:
        rows = (
            Team.query.filter(Team.id.in_(team_ids))
            .order_by(Team.points.desc())
            .limit(6)
            .all()
        )
        next_fixtures = _next_fixture_per_team([r.id for r in rows])
        teams = [{"team": t, "next": next_fixtures.get(t.id)} for t in rows]

    players = []
    if player_ids:
        rows = (
            Player.query.filter(Player.id.in_(player_ids), Player.team_id.is_not(None))
            .limit(6)
            .all()
        )
        players = [{"player": p} for p in rows if p.team is not None]

    return {
        "tournaments": tournaments,
        "teams": teams,
        "players": players,
        "any": bool(tournaments or teams or players),
    }


def _latest_match_per_tournament(tournament_ids):
    if not tournament_ids:
        return {}
    rows = (
        Match.query.filter(Match.tournament_id.in_(tournament_ids))
        .order_by(Match.scheduled_at.desc())
        .all()
    )
    out: dict[int, Match] = {}
    for m in rows:
        out.setdefault(m.tournament_id, m)
    return out


def _next_fixture_per_team(team_ids):
    if not team_ids:
        return {}
    rows = (
        Match.query.filter(
            (Match.team_a_id.in_(team_ids)) | (Match.team_b_id.in_(team_ids)),
            Match.status.in_([MatchStatus.UPCOMING, MatchStatus.LIVE]),
        )
        .order_by(Match.scheduled_at.asc())
        .all()
    )
    out: dict[int, Match] = {}
    for m in rows:
        for tid in (m.team_a_id, m.team_b_id):
            if tid in team_ids and tid not in out:
                out[tid] = m
    return out


def _build_conversations():
    """Match/tournament threads the user has commented in, plus the latest reply."""
    my_comments = (
        Comment.query.filter_by(user_id=current_user.id)
        .order_by(Comment.created_at.desc())
        .limit(40)
        .all()
    )

    seen: set[tuple[str, int]] = set()
    threads: list[dict] = []
    for c in my_comments:
        if c.match_id is not None:
            key = ("match", c.match_id)
        elif c.tournament_id is not None:
            key = ("tournament", c.tournament_id)
        else:
            continue
        if key in seen:
            continue
        seen.add(key)

        if key[0] == "match":
            match = c.match
            if match is None:
                continue
            latest = (
                Comment.query.filter_by(match_id=match.id)
                .order_by(Comment.created_at.desc())
                .first()
            )
            new_count = Comment.query.filter(
                Comment.match_id == match.id,
                Comment.created_at > c.created_at,
                Comment.user_id != current_user.id,
            ).count()
            threads.append(
                {
                    "title": f"{match.team_a.name} vs {match.team_b.name}",
                    "context": match.tournament.name,
                    "url": url_for(
                        "matches.scorecard",
                        tournament_id=match.tournament_id,
                        match_id=match.id,
                    ),
                    "latest_author": latest.user.display_name if latest else None,
                    "latest_body": latest.body if latest else None,
                    "new_count": new_count,
                }
            )
        else:
            tournament = c.tournament
            if tournament is None:
                continue
            latest = (
                Comment.query.filter_by(tournament_id=tournament.id)
                .order_by(Comment.created_at.desc())
                .first()
            )
            new_count = Comment.query.filter(
                Comment.tournament_id == tournament.id,
                Comment.created_at > c.created_at,
                Comment.user_id != current_user.id,
            ).count()
            threads.append(
                {
                    "title": tournament.name,
                    "context": "Tournament discussion",
                    "url": url_for("tournaments.detail", tournament_id=tournament.id),
                    "latest_author": latest.user.display_name if latest else None,
                    "latest_body": latest.body if latest else None,
                    "new_count": new_count,
                }
            )
        if len(threads) >= 5:
            break

    return threads


def _profile_completion(user: User) -> dict:
    fields = [
        ("Display name", bool(user.display_name)),
        ("Avatar", bool(user.avatar_url)),
        ("Location", bool(user.location)),
        ("Bio", bool(user.bio)),
    ]
    done = sum(1 for _, ok in fields if ok)
    return {
        "done": done,
        "total": len(fields),
        "percent": round(done / len(fields) * 100),
        "missing": [name for name, ok in fields if not ok],
    }


@bp.route("/users/<int:user_id>")
def profile(user_id: int):
    user = db.session.get(User, user_id) or abort(404)
    organised = (
        Tournament.query.filter_by(organiser_id=user.id)
        .order_by(Tournament.start_date.desc())
        .all()
    )
    stats = {
        "tournaments_organised": len(organised),
        "matches_recorded": Match.query.filter(
            Match.tournament_id.in_([t.id for t in organised]) if organised else False,
            Match.status == MatchStatus.COMPLETED,
        ).count(),
        "titles_won": sum(
            1 for t in organised if t.status == TournamentStatus.COMPLETED
        ),
    }
    return render_template(
        "users/profile.html",
        user=user,
        organised=organised,
        stats=stats,
        is_self=current_user.is_authenticated and current_user.id == user.id,
    )


@bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    form = ProfileEditForm(obj=current_user)
    if form.validate_on_submit():
        new_email = form.email.data.lower().strip()
        if new_email != current_user.email:
            taken = User.query.filter(
                User.email == new_email, User.id != current_user.id
            ).first()
            if taken:
                form.email.errors.append("Email already in use.")
                return render_template("users/profile_edit.html", form=form)
        current_user.display_name = form.display_name.data.strip()
        current_user.email = new_email
        current_user.location = (form.location.data or "").strip() or None
        current_user.bio = (form.bio.data or "").strip() or None
        current_user.avatar_url = (form.avatar_url.data or "").strip() or None
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("users.profile", user_id=current_user.id))
    return render_template("users/profile_edit.html", form=form)
