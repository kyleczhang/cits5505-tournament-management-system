"""Tournament creation flow using reusable existing teams."""

from __future__ import annotations

from datetime import date, datetime

import criktrack.tournaments.routes as tournament_routes
from criktrack.extensions import db
from criktrack.models import (
    Match,
    MatchStatus,
    Role,
    Team,
    Tournament,
    TournamentFormat,
    TournamentStatus,
    TournamentTeam,
)


def _scaffold_tournament(make_user):
    """Build test helper state for scaffold tournament."""
    organiser = make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    tournament = Tournament(
        name="Fixture Cup",
        format=TournamentFormat.ROUND_ROBIN,
        status=TournamentStatus.UPCOMING,
        start_date=date(2026, 8, 1),
        team_count=1,
        organiser_id=organiser.id,
    )
    db.session.add(tournament)
    db.session.flush()

    team_a = Team(organiser_id=organiser.id, name="Alpha", short_code="ALP")
    team_b = Team(organiser_id=organiser.id, name="Bravo", short_code="BRV")
    db.session.add_all([team_a, team_b])
    db.session.flush()
    db.session.add(TournamentTeam(tournament_id=tournament.id, team_id=team_a.id))
    db.session.commit()
    return organiser, tournament, team_a, team_b


def test_tournament_create_lists_only_current_organisers_teams(
    client, app, make_user, login
):
    """Test that tournament create lists only current organisers teams."""
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
    """Test that organiser can create tournament from existing teams."""
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


def test_organiser_can_create_tournament_with_default_venue(
    client, app, make_user, login, monkeypatch
):
    """Test that organiser can create tournament with default venue."""
    organiser = make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    team_a = Team(organiser_id=organiser.id, name="Alpha", short_code="ALP")
    team_b = Team(organiser_id=organiser.id, name="Bravo", short_code="BRV")
    db.session.add_all([team_a, team_b])
    db.session.commit()
    monkeypatch.setattr(tournament_routes, "geocode_address", lambda _: (-31.95, 115.86))

    login("org@example.com")
    resp = client.post(
        "/tournaments/create",
        data={
            "name": "Fixture Cup",
            "start_date": "2026-08-01",
            "format": "round_robin",
            "overs": "20",
            "team_ids": [str(team_a.id), str(team_b.id)],
            "venue_name": "UWA Sports Park",
            "venue_address": "Hackett Dr, Crawley WA 6009",
        },
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    tournament = Tournament.query.filter_by(name="Fixture Cup").first()
    assert tournament is not None
    assert tournament.venue is not None
    assert tournament.venue.name == "UWA Sports Park"
    assert tournament.venue.address == "Hackett Dr, Crawley WA 6009"
    assert tournament.venue.lat == -31.95
    assert tournament.venue.lng == 115.86


def test_organiser_can_add_existing_team_to_tournament(client, app, make_user, login):
    """Test that organiser can add existing team to tournament."""
    _, tournament, _, team_b = _scaffold_tournament(make_user)
    login("org@example.com")

    resp = client.post(
        f"/tournaments/{tournament.id}/teams/add",
        data={"team_id": str(team_b.id)},
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    entry = TournamentTeam.query.filter_by(
        tournament_id=tournament.id, team_id=team_b.id
    ).first()
    assert entry is not None
    db.session.refresh(tournament)
    assert tournament.team_count == 2


def test_tournament_detail_shows_team_management_for_organiser(
    client, app, make_user, login
):
    """Test that tournament detail shows team management for organiser."""
    _, tournament, team_a, team_b = _scaffold_tournament(make_user)
    login("org@example.com")

    body = client.get(f"/tournaments/{tournament.id}").data.decode()

    assert "Participating teams" in body
    assert team_a.name in body
    assert team_b.name in body
    assert "Add team" in body


def test_organiser_cannot_add_foreign_team_to_tournament(client, app, make_user, login):
    """Test that organiser cannot add foreign team to tournament."""
    _, tournament, _, _ = _scaffold_tournament(make_user)
    other = make_user("other@example.com", role=Role.ORGANIZER, display_name="Other")
    foreign_team = Team(organiser_id=other.id, name="Sharks", short_code="SHK")
    db.session.add(foreign_team)
    db.session.commit()
    login("org@example.com")

    resp = client.post(
        f"/tournaments/{tournament.id}/teams/add",
        data={"team_id": str(foreign_team.id)},
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    entry = TournamentTeam.query.filter_by(
        tournament_id=tournament.id, team_id=foreign_team.id
    ).first()
    assert entry is None
    db.session.refresh(tournament)
    assert tournament.team_count == 1


def test_organiser_can_remove_team_before_fixtures_exist(client, app, make_user, login):
    """Test that organiser can remove team before fixtures exist."""
    _, tournament, team_a, team_b = _scaffold_tournament(make_user)
    db.session.add(TournamentTeam(tournament_id=tournament.id, team_id=team_b.id))
    db.session.commit()
    login("org@example.com")

    resp = client.post(
        f"/tournaments/{tournament.id}/teams/{team_b.id}/remove",
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    entry = TournamentTeam.query.filter_by(
        tournament_id=tournament.id, team_id=team_b.id
    ).first()
    assert entry is None
    still_registered = TournamentTeam.query.filter_by(
        tournament_id=tournament.id, team_id=team_a.id
    ).first()
    assert still_registered is not None
    db.session.refresh(tournament)
    assert tournament.team_count == 1


def test_organiser_cannot_remove_team_with_existing_fixture(client, app, make_user, login):
    """Test that organiser cannot remove team with existing fixture."""
    _, tournament, team_a, team_b = _scaffold_tournament(make_user)
    db.session.add(TournamentTeam(tournament_id=tournament.id, team_id=team_b.id))
    db.session.flush()
    db.session.add(
        Match(
            tournament_id=tournament.id,
            team_a_id=team_a.id,
            team_b_id=team_b.id,
            scheduled_at=datetime(2026, 8, 2, 14, 0),
            status=MatchStatus.UPCOMING,
        )
    )
    db.session.commit()
    login("org@example.com")

    resp = client.post(f"/tournaments/{tournament.id}/teams/{team_b.id}/remove")

    assert resp.status_code in (302, 303)
    entry = TournamentTeam.query.filter_by(
        tournament_id=tournament.id, team_id=team_b.id
    ).first()
    assert entry is not None
