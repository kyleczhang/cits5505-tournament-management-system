"""Match routes — organiser fixture creation and roster-based result entry."""

from __future__ import annotations

from datetime import date

import criktrack.matches.routes as match_routes
from criktrack.extensions import db
from criktrack.models import (
    Match,
    MatchStatus,
    Player,
    PlayerRole,
    Role,
    Team,
    Tournament,
    TournamentFormat,
    TournamentStatus,
    TournamentTeam,
    Venue,
)


def _scaffold(make_user, with_default_venue: bool = False):
    """Build test helper state for scaffold."""
    organiser = make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    venue = None
    if with_default_venue:
        venue = Venue(
            name="UWA Sports Park",
            address="Hackett Dr, Crawley WA 6009",
            lat=-31.95,
            lng=115.86,
        )
        db.session.add(venue)
        db.session.flush()
    tournament = Tournament(
        name="Fixture Cup",
        format=TournamentFormat.ROUND_ROBIN,
        status=TournamentStatus.UPCOMING,
        start_date=date(2026, 7, 1),
        team_count=2,
        organiser_id=organiser.id,
        venue_id=venue.id if venue else None,
    )
    db.session.add(tournament)
    db.session.flush()

    team_a = Team(organiser_id=organiser.id, name="Alpha", short_code="ALP")
    team_b = Team(organiser_id=organiser.id, name="Bravo", short_code="BRV")
    db.session.add_all([team_a, team_b])
    db.session.flush()
    db.session.add_all(
        [
            TournamentTeam(tournament_id=tournament.id, team_id=team_a.id),
            TournamentTeam(tournament_id=tournament.id, team_id=team_b.id),
        ]
    )
    db.session.add_all(
        [
            Player(team_id=team_a.id, name="A Batter", role=PlayerRole.BATTER),
            Player(team_id=team_b.id, name="B Bowler", role=PlayerRole.BOWLER),
        ]
    )
    db.session.commit()
    return tournament, team_a, team_b


def test_organiser_can_create_match(client, app, make_user, login):
    """Test that organiser can create match."""
    tournament, team_a, team_b = _scaffold(make_user)
    login("org@example.com")

    resp = client.post(
        f"/tournaments/{tournament.id}/matches/create",
        data={
            "team_a_id": team_a.id,
            "team_b_id": team_b.id,
            "scheduled_at": "2026-07-02T14:00",
        },
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    match = Match.query.filter_by(tournament_id=tournament.id).first()
    assert match is not None
    assert match.team_a_id == team_a.id
    assert match.team_b_id == team_b.id
    assert match.status == MatchStatus.UPCOMING


def test_match_create_inherits_tournament_default_venue(client, app, make_user, login):
    """Test that match create inherits tournament default venue."""
    tournament, team_a, team_b = _scaffold(make_user, with_default_venue=True)
    login("org@example.com")

    resp = client.post(
        f"/tournaments/{tournament.id}/matches/create",
        data={
            "team_a_id": team_a.id,
            "team_b_id": team_b.id,
            "scheduled_at": "2026-07-02T14:00",
        },
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    match = Match.query.filter_by(tournament_id=tournament.id).first()
    assert match is not None
    assert match.venue_id == tournament.venue_id


def test_match_create_can_override_tournament_default_venue(
    client, app, make_user, login, monkeypatch
):
    """Test that match create can override tournament default venue."""
    tournament, team_a, team_b = _scaffold(make_user, with_default_venue=True)
    monkeypatch.setattr(match_routes, "geocode_address", lambda _: (-32.05, 115.75))
    login("org@example.com")

    resp = client.post(
        f"/tournaments/{tournament.id}/matches/create",
        data={
            "team_a_id": team_a.id,
            "team_b_id": team_b.id,
            "scheduled_at": "2026-07-02T14:00",
            "venue_name": "Fremantle Oval",
            "venue_address": "Fremantle WA 6160",
        },
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    match = Match.query.filter_by(tournament_id=tournament.id).first()
    assert match is not None
    assert match.venue_id != tournament.venue_id
    assert match.venue is not None
    assert match.venue.name == "Fremantle Oval"
    assert match.venue.address == "Fremantle WA 6160"
    assert match.venue.lat == -32.05
    assert match.venue.lng == 115.75


def test_match_create_rejects_partial_venue_override(client, app, make_user, login):
    """Test that match create rejects partial venue override."""
    tournament, team_a, team_b = _scaffold(make_user, with_default_venue=True)
    login("org@example.com")

    resp = client.post(
        f"/tournaments/{tournament.id}/matches/create",
        data={
            "team_a_id": team_a.id,
            "team_b_id": team_b.id,
            "scheduled_at": "2026-07-02T14:00",
            "venue_name": "Fremantle Oval",
            "venue_address": "",
        },
        follow_redirects=False,
    )

    assert resp.status_code == 200
    assert Match.query.filter_by(tournament_id=tournament.id).count() == 0
    assert b"Enter a venue address or leave both venue fields blank." in resp.data


def test_record_page_uses_roster_selectors(client, app, make_user, login):
    """Test that record page uses roster selectors."""
    tournament, team_a, team_b = _scaffold(make_user)
    match = Match(
        tournament_id=tournament.id,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        status=MatchStatus.LIVE,
    )
    db.session.add(match)
    db.session.commit()
    login("org@example.com")

    resp = client.get(f"/tournaments/{tournament.id}/matches/{match.id}/record")
    body = resp.data.decode()
    assert 'data-field="player_id"' in body
    assert "Select batter" in body
    assert "Select bowler" in body


def test_organiser_can_start_upcoming_match(client, app, make_user, login):
    """Test that organiser can start upcoming match."""
    tournament, team_a, team_b = _scaffold(make_user)
    match = Match(
        tournament_id=tournament.id,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        status=MatchStatus.UPCOMING,
    )
    db.session.add(match)
    db.session.commit()
    login("org@example.com")

    resp = client.post(
        f"/tournaments/{tournament.id}/matches/{match.id}/start",
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    db.session.refresh(match)
    db.session.refresh(tournament)
    assert match.status == MatchStatus.LIVE
    assert tournament.status == TournamentStatus.LIVE


def test_other_organiser_cannot_start_foreign_match(client, app, make_user, login):
    """Test that other organiser cannot start foreign match."""
    tournament, team_a, team_b = _scaffold(make_user)
    make_user("other@example.com", role=Role.ORGANIZER, display_name="Other Org")
    match = Match(
        tournament_id=tournament.id,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        status=MatchStatus.UPCOMING,
    )
    db.session.add(match)
    db.session.commit()
    login("other@example.com")

    resp = client.post(f"/tournaments/{tournament.id}/matches/{match.id}/start")

    assert resp.status_code == 403
