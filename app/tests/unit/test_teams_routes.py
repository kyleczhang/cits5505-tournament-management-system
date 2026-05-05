"""Teams blueprint — organiser team and roster management flows."""

from __future__ import annotations

from criktrack.extensions import db
from criktrack.models import Player, PlayerRole, Role, Team


def test_organiser_can_create_team(client, app, make_user, login):
    make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    login("org@example.com")

    resp = client.post(
        "/teams/create",
        data={"name": "UWA Thunder", "short_code": "UWT"},
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    team = Team.query.filter_by(name="UWA Thunder").first()
    assert team is not None
    assert team.short_code == "UWT"


def test_team_list_only_shows_current_organisers_teams(client, app, make_user, login):
    org_a = make_user("a@example.com", role=Role.ORGANIZER, display_name="Org A")
    org_b = make_user("b@example.com", role=Role.ORGANIZER, display_name="Org B")
    db.session.add_all(
        [
            Team(organiser_id=org_a.id, name="Alpha", short_code="ALP"),
            Team(organiser_id=org_b.id, name="Bravo", short_code="BRV"),
        ]
    )
    db.session.commit()

    login("a@example.com")
    body = client.get("/teams").data.decode()
    assert "Alpha" in body
    assert "Bravo" not in body


def test_organiser_can_add_player_to_team_roster(client, app, make_user, login):
    organiser = make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    team = Team(organiser_id=organiser.id, name="Alpha", short_code="ALP")
    db.session.add(team)
    db.session.commit()
    login("org@example.com")

    resp = client.post(
        f"/teams/{team.id}/players/add",
        data={"name": "Aarav Sharma", "role": PlayerRole.BATTER.value},
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    player = Player.query.filter_by(team_id=team.id, name="Aarav Sharma").first()
    assert player is not None
    assert player.role == PlayerRole.BATTER
