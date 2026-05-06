"""Teams blueprint — organiser team and roster management flows."""

from __future__ import annotations

from datetime import date

from criktrack.extensions import db
from criktrack.models import (
    BattingEntry,
    Innings,
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
)


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


def test_edit_team_cancel_links_back_to_team_detail(client, app, make_user, login):
    organiser = make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    team = Team(organiser_id=organiser.id, name="Alpha", short_code="ALP")
    db.session.add(team)
    db.session.commit()
    login("org@example.com")

    resp = client.get(f"/teams/{team.id}/edit")

    assert resp.status_code == 200
    assert f'/teams/{team.id}"'.encode() in resp.data


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


def test_organiser_can_delete_unused_team(client, app, make_user, login):
    organiser = make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    team = Team(organiser_id=organiser.id, name="Alpha", short_code="ALP")
    db.session.add(team)
    db.session.commit()
    login("org@example.com")

    resp = client.post(f"/teams/{team.id}/delete", follow_redirects=False)

    assert resp.status_code in (302, 303)
    assert db.session.get(Team, team.id) is None


def test_organiser_cannot_delete_team_registered_in_tournament(
    client, app, make_user, login
):
    organiser = make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    team = Team(organiser_id=organiser.id, name="Alpha", short_code="ALP")
    tournament = Tournament(
        name="Fixture Cup",
        format=TournamentFormat.ROUND_ROBIN,
        status=TournamentStatus.UPCOMING,
        start_date=date(2026, 9, 1),
        team_count=1,
        organiser_id=organiser.id,
    )
    db.session.add_all([team, tournament])
    db.session.flush()
    db.session.add(TournamentTeam(tournament_id=tournament.id, team_id=team.id))
    db.session.commit()
    login("org@example.com")

    resp = client.post(f"/teams/{team.id}/delete", follow_redirects=False)

    assert resp.status_code in (302, 303)
    assert db.session.get(Team, team.id) is not None


def test_team_detail_shows_delete_tooltip_for_registered_team(
    client, app, make_user, login
):
    organiser = make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    team = Team(organiser_id=organiser.id, name="Alpha", short_code="ALP")
    tournament = Tournament(
        name="Fixture Cup",
        format=TournamentFormat.ROUND_ROBIN,
        status=TournamentStatus.UPCOMING,
        start_date=date(2026, 9, 1),
        team_count=1,
        organiser_id=organiser.id,
    )
    db.session.add_all([team, tournament])
    db.session.flush()
    db.session.add(TournamentTeam(tournament_id=tournament.id, team_id=team.id))
    db.session.commit()
    login("org@example.com")

    resp = client.get(f"/teams/{team.id}")

    assert resp.status_code == 200
    assert (
        b"This team is registered in one or more tournaments. Remove those "
        b"registrations before deleting it."
    ) in resp.data


def test_other_organiser_cannot_delete_foreign_team(client, app, make_user, login):
    owner = make_user("owner@example.com", role=Role.ORGANIZER, display_name="Owner")
    make_user("other@example.com", role=Role.ORGANIZER, display_name="Other")
    team = Team(organiser_id=owner.id, name="Alpha", short_code="ALP")
    db.session.add(team)
    db.session.commit()
    login("other@example.com")

    resp = client.post(f"/teams/{team.id}/delete")

    assert resp.status_code == 403


def test_organiser_cannot_remove_player_with_scorecard_history(
    client, app, make_user, login
):
    organiser = make_user("org@example.com", role=Role.ORGANIZER, display_name="Org User")
    team_a = Team(organiser_id=organiser.id, name="Alpha", short_code="ALP")
    team_b = Team(organiser_id=organiser.id, name="Bravo", short_code="BRV")
    tournament = Tournament(
        name="Fixture Cup",
        format=TournamentFormat.ROUND_ROBIN,
        status=TournamentStatus.UPCOMING,
        start_date=date(2026, 9, 1),
        team_count=2,
        organiser_id=organiser.id,
    )
    db.session.add_all([team_a, team_b, tournament])
    db.session.flush()
    db.session.add_all(
        [
            TournamentTeam(tournament_id=tournament.id, team_id=team_a.id),
            TournamentTeam(tournament_id=tournament.id, team_id=team_b.id),
        ]
    )
    player = Player(team_id=team_a.id, name="Aarav Sharma", role=PlayerRole.BATTER)
    db.session.add(player)
    db.session.flush()
    match = Match(
        tournament_id=tournament.id,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        status=MatchStatus.COMPLETED,
    )
    db.session.add(match)
    db.session.flush()
    innings = Innings(
        match_id=match.id,
        inning_number=1,
        batting_team_id=team_a.id,
        bowling_team_id=team_b.id,
        runs=120,
        wickets=4,
        overs=20,
    )
    db.session.add(innings)
    db.session.flush()
    db.session.add(
        BattingEntry(
            innings_id=innings.id,
            player_id=player.id,
            runs=42,
            balls=30,
            fours=4,
            sixes=1,
        )
    )
    db.session.commit()
    login("org@example.com")

    resp = client.post(
        f"/teams/{team_a.id}/players/{player.id}/delete",
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    assert db.session.get(Player, player.id) is not None
