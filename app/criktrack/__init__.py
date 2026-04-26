from __future__ import annotations

from config import BaseConfig, get_config
from flask import Flask, render_template


def create_app(config_class: type[BaseConfig] | None = None) -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class or get_config())

    @app.route("/")
    def landing():
        return render_template("landing.html")

    return app
