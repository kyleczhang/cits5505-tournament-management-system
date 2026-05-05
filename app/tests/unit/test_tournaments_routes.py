"""Tournament creation flow using reusable existing teams."""

from __future__ import annotations

from criktrack.extensions import db
from criktrack.models import Role, Team, Tournament, TournamentTeam


def test_tournament_create_lists_only_current_organisers_teams(
    client, app, make_user, login
):
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
    body = client.get("/tournaments/create").data.decode()
    assert "Alpha" in body
    assert "Bravo" not in body


def test_organiser_can_create_tournament_from_existing_teams(
    client, app, make_user, login
):
    organiser = make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    team_a = Team(organiser_id=organiser.id, name="Alpha", short_code="ALP")
    team_b = Team(organiser_id=organiser.id, name="Bravo", short_code="BRV")
    db.session.add_all([team_a, team_b])
    db.session.commit()

    login("org@example.com")
    resp = client.post(
        "/tournaments/create",
        data={
            "name": "Fixture Cup",
            "start_date": "2026-08-01",
            "format": "round_robin",
            "overs": "20",
            "team_ids": [str(team_a.id), str(team_b.id)],
        },
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    tournament = Tournament.query.filter_by(name="Fixture Cup").first()
    assert tournament is not None
    entries = TournamentTeam.query.filter_by(tournament_id=tournament.id).all()
    assert {entry.team_id for entry in entries} == {team_a.id, team_b.id}
    assert tournament.team_count == 2
