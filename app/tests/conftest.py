"""Shared pytest fixtures for unit + selenium suites."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure the `app/` directory is on sys.path so `import criktrack` resolves
# regardless of how pytest is invoked.
_APP_DIR = Path(__file__).resolve().parent.parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

os.environ.setdefault("FLASK_ENV", "testing")

from config import TestConfig  # noqa: E402
from criktrack import create_app  # noqa: E402
from criktrack.extensions import db as _db  # noqa: E402
from criktrack.integrations import cricketdata as _cricketdata  # noqa: E402
from criktrack.models import Role, User  # noqa: E402


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
        _cricketdata.reset_cache()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_user(app):
    def _make(
        email: str,
        password: str = "secret123",
        role: Role = Role.USER,
        display_name: str = "Test User",
    ) -> User:
        user = User(email=email.lower(), display_name=display_name, role=role)
        user.set_password(password)
        _db.session.add(user)
        _db.session.commit()
        return user

    return _make


@pytest.fixture
def login(client):
    def _login(email: str, password: str = "secret123") -> None:
        resp = client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=False,
        )
        assert resp.status_code in (302, 303), resp.data

    return _login
