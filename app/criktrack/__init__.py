from __future__ import annotations

from flask import Flask, render_template, url_for

from config import BaseConfig, get_config

from .extensions import csrf, db, login_manager, migrate
from .filters import register_filters


def create_app(config_class: type[BaseConfig] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class or get_config())

    _ensure_instance_path(app)
    _bind_extensions(app)
    _register_blueprints(app)
    register_filters(app)
    _register_context_processors(app)
    _register_cli(app)
    _register_security_headers(app)

    @app.route("/")
    def landing():  # noqa: WPS430 — small inline route is fine
        return render_template("landing.html")

    return app


def _ensure_instance_path(app: Flask) -> None:
    import os

    os.makedirs(app.instance_path, exist_ok=True)


def _bind_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Importing the models package registers every model with SQLAlchemy and
    # makes them visible to Flask-Migrate's autogenerate.
    from . import models  # noqa: F401

    @login_manager.user_loader
    def _load_user(user_id: str):
        return db.session.get(models.User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    from .auth import bp as auth_bp
    from .comments import bp as comments_bp
    from .errors import bp as errors_bp
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
    app.register_blueprint(live_bp, url_prefix="/api/live")
    app.register_blueprint(errors_bp)


def _register_context_processors(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        return {
            "ctm_config": {
                "googleMapsApiKey": app.config.get("GOOGLE_MAPS_API_KEY", ""),
                "liveFeedEndpoint": url_for("live.matches"),
                "liveFeedPollMs": app.config.get("LIVE_FEED_POLL_MS", 30000),
            },
        }


def _register_cli(app: Flask) -> None:
    from .seed import seed_cli

    app.cli.add_command(seed_cli)


def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def _apply_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        return response
