from __future__ import annotations

from urllib.parse import urlparse

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import Role, User
from . import bp
from .forms import LoginForm, RegisterForm


def _safe_next(target: str | None) -> str | None:
    """Only honour ?next= when it points back to this host (open-redirect guard)."""
    if not target:
        return None
    parsed = urlparse(target)
    if parsed.netloc and parsed.netloc != request.host:
        return None
    if not parsed.path.startswith("/"):
        return None
    return target


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("users.dashboard"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            form.email.errors.append("That email is already registered.")
        else:
            invite = (form.invite_code.data or "").strip()
            configured_invite = current_app.config.get("ORGANIZER_INVITE_CODE", "")
            role = (
                Role.ORGANIZER
                if configured_invite and invite == configured_invite
                else Role.USER
            )
            user = User(
                display_name=form.display_name.data.strip(),
                email=form.email.data.lower().strip(),
                role=role,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f"Welcome, {user.display_name}!", "success")
            return redirect(url_for("users.dashboard"))

    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("users.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user is None or not user.check_password(form.password.data):
            # Identical message regardless of which field was wrong.
            flash("Invalid email or password.", "danger")
        else:
            login_user(user, remember=bool(form.remember.data))
            target = _safe_next(request.args.get("next")) or url_for("users.dashboard")
            return redirect(target)

    return render_template("auth/login.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("landing"))
