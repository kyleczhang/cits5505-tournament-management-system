"""Match routes — organiser fixture creation and roster-based result entry."""

from __future__ import annotations

from datetime import date

from criktrack.extensions import db
from criktrack.models import Match, MatchStatus, Player, PlayerRole, Role, Team, Tournament, TournamentFormat, TournamentStatus, TournamentTeam


def _scaffold(make_user):
    organiser = make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    tournament = Tournament(
        name="Fixture Cup",
        format=TournamentFormat.ROUND_ROBIN,
        status=TournamentStatus.UPCOMING,
        start_date=date(2026, 7, 1),
        team_count=2,
        organiser_id=organiser.id,
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


def test_record_page_uses_roster_selectors(client, app, make_user, login):
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
