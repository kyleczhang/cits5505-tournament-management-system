from __future__ import annotations

from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Match, MatchStatus, Tournament, TournamentStatus, User
from . import bp
from .forms import ProfileEditForm


@bp.route("/dashboard")
@login_required
def dashboard():
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

    summary = {
        "my_tournaments": len(organised),
        "upcoming_matches": len(upcoming_matches),
        "recent_results": len(recent_results),
        "total_players": sum(
            len(team.players) for t in organised for team in t.teams
        ),
    }

    return render_template(
        "dashboard.html",
        organised=organised,
        upcoming_matches=upcoming_matches,
        recent_results=recent_results,
        summary=summary,
    )


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
            Match.tournament_id.in_([t.id for t in organised])
            if organised else False,
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
