"""User profile routes — editing profile fields and avatar theme."""

from __future__ import annotations

from criktrack.extensions import db
from criktrack.models import User


def test_profile_edit_saves_avatar_color(client, app, make_user, login):
    """Test that profile edit saves avatar color."""
    user = make_user("fan@example.com", password="secret123", display_name="Fan User")
    login("fan@example.com", "secret123")

    resp = client.post(
        "/profile/edit",
        data={
            "display_name": "Updated Fan",
            "email": "fan@example.com",
            "location": "Perth",
            "bio": "Loves a tight chase.",
            "avatar_color": "violet",
        },
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    db.session.refresh(user)
    assert user.display_name == "Updated Fan"
    assert user.avatar_color == "violet"


def test_profile_edit_rejects_invalid_avatar_color(client, app, make_user, login):
    """Test that profile edit rejects invalid avatar color."""
    user = make_user("fan2@example.com", password="secret123", display_name="Fan Two")
    login("fan2@example.com", "secret123")

    resp = client.post(
        "/profile/edit",
        data={
            "display_name": "Fan Two",
            "email": "fan2@example.com",
            "location": "",
            "bio": "",
            "avatar_color": "neon-green",
        },
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"Not a valid choice." in resp.data
    refreshed = db.session.get(User, user.id)
    assert refreshed.avatar_color == "amber"
