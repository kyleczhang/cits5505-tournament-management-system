"""Comments API — auth + validation + persistence."""

from __future__ import annotations

from datetime import date, datetime

from criktrack.extensions import db
from criktrack.models import (
    Match,
    Role,
    Team,
    Tournament,
    TournamentFormat,
    TournamentStatus,
    User,
)


def _scaffold(organiser_email: str = "org@example.com"):
    organiser = User(
        email=organiser_email, display_name="Org", role=Role.ORGANIZER
    )
    organiser.set_password("secret123")
    db.session.add(organiser)
    db.session.flush()

    tournament = Tournament(
        name="Super Cup",
        format=TournamentFormat.ROUND_ROBIN,
        status=TournamentStatus.UPCOMING,
        start_date=date(2026, 5, 1),
        team_count=2,
        organiser_id=organiser.id,
    )
    db.session.add(tournament)
    db.session.flush()

    team_a = Team(tournament_id=tournament.id, name="A", short_code="AAA")
    team_b = Team(tournament_id=tournament.id, name="B", short_code="BBB")
    db.session.add_all([team_a, team_b])
    db.session.flush()

    match = Match(
        tournament_id=tournament.id,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        scheduled_at=datetime(2026, 5, 2, 14, 0),
    )
    db.session.add(match)
    db.session.commit()
    return tournament, match


def test_list_match_comments_returns_empty_array(client, app):
    _, match = _scaffold()
    resp = client.get(f"/api/matches/{match.id}/comments")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_post_comment_requires_authentication(client, app):
    _, match = _scaffold()
    resp = client.post(
        f"/api/matches/{match.id}/comments",
        json={"body": "Great match!"},
    )
    # CSRF is disabled in TestConfig so the rejection comes from the auth check.
    assert resp.status_code in (401, 403)


def test_authenticated_user_can_post_and_fetch_comment(client, app, make_user, login):
    tournament, match = _scaffold()
    make_user("fan@example.com", password="secret123")
    login("fan@example.com", "secret123")

    post = client.post(
        f"/api/matches/{match.id}/comments",
        json={"body": "Thrilling finish!"},
    )
    assert post.status_code == 201
    assert post.get_json()["body"] == "Thrilling finish!"

    get = client.get(f"/api/matches/{match.id}/comments")
    body = get.get_json()
    assert len(body) == 1
    assert body[0]["body"] == "Thrilling finish!"


def test_comment_length_limit_enforced(client, app, make_user, login):
    _, match = _scaffold()
    make_user("fan2@example.com", password="secret123")
    login("fan2@example.com", "secret123")
    resp = client.post(
        f"/api/matches/{match.id}/comments",
        json={"body": "x" * 600},
    )
    assert resp.status_code == 400
