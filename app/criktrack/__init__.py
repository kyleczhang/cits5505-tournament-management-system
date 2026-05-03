from __future__ import annotations

from flask import Flask, render_template, url_for

from config import BaseConfig, get_config

from .extensions import csrf, db, login_manager, migrate
from .filters import register_filters


def create_app(config_class: type[BaseConfig] | None = None) -> Flask:
    """Create and configure the Flask application instance."""
    # Set instance_relative_config to True to resolve relative config files from
    # the instance folder.
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class or get_config())

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY is not set. Add it to your environment or .env file "
            "(see app/.env.example)."
        )

    _ensure_instance_path(app)
    _bind_extensions(app)
    _register_blueprints(app)
    register_filters(app)
    _register_context_processors(app)
    _register_cli(app)
    _register_security_headers(app)

    @app.route("/")
    def landing():
        return render_template("landing.html")

    return app


def _ensure_instance_path(app: Flask) -> None:
    """Create the Flask instance directory if it does not already exist."""
    import os

    os.makedirs(app.instance_path, exist_ok=True)


def _bind_extensions(app: Flask) -> None:
    """Initialise delayed-bind extensions for the app factory instance.

    In this project we use the app factory pattern: ``create_app()`` builds the
    Flask app at runtime, so extensions are created once in ``extensions.py``
    and attached later via ``init_app(app)`` instead of being bound eagerly to
    a single global app.
    """
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # This import is used for its side effects: model class definitions such as
    # User(db.Model) run at import time and register tables/metadata with the ORM.
    # Keep it here instead of at module top level so the app factory binds the
    # extensions first and avoids unnecessary import-order coupling.
    from . import models

    # Register the callback Flask-Login calls to turn the session's stored user
    # ID back into the corresponding User model instance on each request.
    @login_manager.user_loader
    def _load_user(user_id: str):
        """Resolve the current session user by primary key."""
        return db.session.get(models.User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    """Register every feature blueprint with its URL prefix."""
    from .auth import bp as auth_bp
    from .comments import bp as comments_bp
    from .errors import bp as errors_bp
    from .follows import bp as follows_bp
    from .live import bp as live_bp
    from .matches import bp as matches_bp
    from .players import bp as players_bp
    from .tournaments import bp as tournaments_bp
    from .users import bp as users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(tournaments_bp, url_prefix="/tournaments")
    app.register_blueprint(matches_bp)
    app.register_blueprint(players_bp)
    app.register_blueprint(comments_bp, url_prefix="/api")
    app.register_blueprint(follows_bp, url_prefix="/api")
    app.register_blueprint(live_bp, url_prefix="/api/live")
    app.register_blueprint(errors_bp)


def _register_context_processors(app: Flask) -> None:
    """Expose frontend configuration shared by templates."""

    @app.context_processor
    def inject_globals():
        """Inject runtime configuration consumed by the UI shell."""
        return {
            "ctm_config": {
                "googleMapsApiKey": app.config.get("GOOGLE_MAPS_API_KEY", ""),
                "liveFeedEndpoint": url_for("live.matches"),
                "liveFeedPollMs": app.config.get("LIVE_FEED_POLL_MS", 30000),
            },
        }


def _register_cli(app: Flask) -> None:
    """Register project-specific CLI commands."""
    from .seed import seed_cli

    app.cli.add_command(seed_cli)


def _register_security_headers(app: Flask) -> None:
    """Register an after-request hook that adds default security headers."""

    @app.after_request
    def _apply_headers(response):
        """Attach default security headers to the outgoing response."""
        # Tell browsers to trust the declared Content-Type and not MIME-sniff.
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # Only allow same-origin framing to reduce clickjacking risk.
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        # Limit how much referrer information is sent cross-origin.
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        # Disable unused high-privilege browser features by default.
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        return response
