"""Auth flow: register, login, open-redirect guard, organizer invite."""

from __future__ import annotations

from criktrack.auth.routes import _safe_next
from criktrack.models import Role, User


def test_register_creates_regular_user(client):
    resp = client.post(
        "/register",
        data={
            "display_name": "Alice",
            "email": "alice@example.com",
            "password": "secret123",
            "password_confirm": "secret123",
            "terms": "y",
        },
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    user = User.query.filter_by(email="alice@example.com").first()
    assert user is not None
    assert user.role == Role.USER


def test_register_with_valid_invite_becomes_organizer(client, app):
    assert app.config["ORGANIZER_INVITE_CODE"] == "test-invite"
    resp = client.post(
        "/register",
        data={
            "display_name": "Oscar",
            "email": "oscar@example.com",
            "password": "secret123",
            "password_confirm": "secret123",
            "invite_code": "test-invite",
            "terms": "y",
        },
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    user = User.query.filter_by(email="oscar@example.com").first()
    assert user.role == Role.ORGANIZER


def test_login_rejects_bad_password(client, make_user):
    make_user("bob@example.com", password="secret123")
    resp = client.post(
        "/login",
        data={"email": "bob@example.com", "password": "wrong-pw"},
        follow_redirects=True,
    )
    assert b"Invalid email or password." in resp.data


def test_safe_next_blocks_external_host(app):
    with app.test_request_context("/login"):
        assert _safe_next("https://evil.example/phish") is None
        assert _safe_next("//evil.example/phish") is None
        assert _safe_next("/tournaments") == "/tournaments"
        assert _safe_next(None) is None
