"""Follow API — auth + validation + idempotent toggling."""

from __future__ import annotations

from datetime import date

from criktrack.extensions import db
from criktrack.models import (
    Follow,
    FollowTarget,
    Player,
    PlayerRole,
    Role,
    Team,
    Tournament,
    TournamentFormat,
    TournamentStatus,
    User,
)


def _scaffold():
    organiser = User(email="org@example.com", display_name="Org", role=Role.ORGANIZER)
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

    team = Team(tournament_id=tournament.id, name="A", short_code="AAA")
    db.session.add(team)
    db.session.flush()

    player = Player(team_id=team.id, name="Aarav", role=PlayerRole.BATTER)
    db.session.add(player)
    db.session.commit()
    return tournament, team, player


def test_follow_requires_authentication(client, app):
    tournament, _, _ = _scaffold()
    resp = client.post(
        "/api/follow",
        json={"targetType": "tournament", "targetId": tournament.id},
    )
    assert resp.status_code in (401, 403)


def test_follow_unknown_target_type_rejected(client, app, make_user, login):
    make_user("fan@example.com")
    login("fan@example.com")
    resp = client.post("/api/follow", json={"targetType": "match", "targetId": 1})
    assert resp.status_code == 400


def test_follow_missing_target_returns_404(client, app, make_user, login):
    make_user("fan@example.com")
    login("fan@example.com")
    resp = client.post(
        "/api/follow", json={"targetType": "tournament", "targetId": 9999}
    )
    assert resp.status_code == 404


def test_follow_creates_row_and_is_idempotent(client, app, make_user, login):
    tournament, _, _ = _scaffold()
    make_user("fan@example.com")
    login("fan@example.com")

    r1 = client.post(
        "/api/follow",
        json={"targetType": "tournament", "targetId": tournament.id},
    )
    assert r1.status_code == 200
    assert r1.get_json()["following"] is True
    assert Follow.query.count() == 1

    r2 = client.post(
        "/api/follow",
        json={"targetType": "tournament", "targetId": tournament.id},
    )
    assert r2.status_code == 200
    assert Follow.query.count() == 1


def test_unfollow_removes_row(client, app, make_user, login):
    _, team, _ = _scaffold()
    make_user("fan@example.com")
    login("fan@example.com")

    client.post("/api/follow", json={"targetType": "team", "targetId": team.id})
    assert Follow.query.count() == 1

    resp = client.delete(
        "/api/follow", json={"targetType": "team", "targetId": team.id}
    )
    assert resp.status_code == 200
    assert resp.get_json()["following"] is False
    assert Follow.query.count() == 0


def test_status_endpoint_reports_follow_state(client, app, make_user, login):
    _, _, player = _scaffold()
    make_user("fan@example.com")
    login("fan@example.com")

    pre = client.get(
        "/api/follow/status",
        query_string={"targetType": "player", "targetId": player.id},
    )
    assert pre.get_json() == {"following": False}

    client.post("/api/follow", json={"targetType": "player", "targetId": player.id})

    post = client.get(
        "/api/follow/status",
        query_string={"targetType": "player", "targetId": player.id},
    )
    assert post.get_json() == {"following": True}


def test_follow_targets_are_isolated_per_user(client, app, make_user, login):
    tournament, _, _ = _scaffold()
    make_user("a@example.com")
    make_user("b@example.com")
    login("a@example.com")
    client.post(
        "/api/follow",
        json={"targetType": "tournament", "targetId": tournament.id},
    )

    # log out + log in as different user
    client.post("/logout")
    login("b@example.com")
    status = client.get(
        "/api/follow/status",
        query_string={"targetType": "tournament", "targetId": tournament.id},
    )
    assert status.get_json() == {"following": False}
    assert Follow.query.count() == 1
