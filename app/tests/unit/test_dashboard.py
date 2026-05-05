"""Dashboard route — role-based dispatch + Following widgets render."""

from __future__ import annotations

from datetime import date, datetime

from criktrack.extensions import db
from criktrack.models import (
    Follow,
    FollowTarget,
    Match,
    MatchStatus,
    Player,
    PlayerRole,
    Role,
    Team,
    TournamentTeam,
    Tournament,
    TournamentFormat,
    TournamentStatus,
)


def _seed(make_user):
    """Seed an organiser, a live tournament, two teams, rostered players, and a live match."""
    organiser = make_user(
        "org@example.com", role=Role.ORGANIZER, display_name="Org User"
    )
    tournament = Tournament(
        name="Champions Trophy",
        format=TournamentFormat.ROUND_ROBIN,
        status=TournamentStatus.LIVE,
        start_date=date(2026, 5, 1),
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
    player = Player(team_id=team_a.id, name="Aarav", role=PlayerRole.BATTER)
    second_player = Player(team_id=team_b.id, name="Ben", role=PlayerRole.BOWLER)
    match = Match(
        tournament_id=tournament.id,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        scheduled_at=datetime(2026, 5, 2, 14, 0),
        status=MatchStatus.LIVE,
    )
    db.session.add_all([player, second_player, match])
    db.session.commit()
    return organiser, tournament, team_a, player, second_player, match


def test_organizer_dashboard_renders_workspace(client, app, make_user, login):
    _seed(make_user)
    login("org@example.com")
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "Organiser workspace" in body
    assert "Switch to fan view" in body
    # Live match in own tournament should surface in Needs your attention.
    assert "Needs your attention" in body
    assert "Record now" in body


def test_organizer_record_cta_points_to_record_route(client, app, make_user, login):
    _, tournament, _, _, _, match = _seed(make_user)
    login("org@example.com")
    body = client.get("/dashboard").data.decode()
    record_url = f"/tournaments/{tournament.id}/matches/{match.id}/record"
    assert record_url in body


def test_organizer_fan_view_renders_user_dashboard(client, app, make_user, login):
    _seed(make_user)
    login("org@example.com")
    body = client.get("/dashboard?view=fan").data.decode()
    assert "Fan view" in body
    assert "Back to organiser workspace" in body
    assert "Live cricket around the world" in body


def test_user_dashboard_default_is_fan_view(client, app, make_user, login):
    _seed(make_user)
    make_user("fan@example.com")
    login("fan@example.com")
    body = client.get("/dashboard").data.decode()
    assert "Live cricket around the world" in body
    assert "Organiser workspace" not in body


def test_following_widgets_render_when_user_follows_targets(
    client, app, make_user, login
):
    _, tournament, team, player, _, _ = _seed(make_user)
    fan = make_user("fan@example.com")
    db.session.add_all(
        [
            Follow(
                user_id=fan.id,
                target_type=FollowTarget.TOURNAMENT,
                target_id=tournament.id,
            ),
            Follow(user_id=fan.id, target_type=FollowTarget.TEAM, target_id=team.id),
            Follow(
                user_id=fan.id,
                target_type=FollowTarget.PLAYER,
                target_id=player.id,
            ),
        ]
    )
    db.session.commit()

    login("fan@example.com")
    body = client.get("/dashboard").data.decode()
    assert "Tournaments you follow" in body
    assert "Teams you follow" in body
    assert "Players you follow" in body
    assert tournament.name in body
    assert team.name in body
    assert player.name in body


def test_dashboard_skips_followed_player_without_tournament_entry(
    client, app, make_user, login
):
    """A followed player whose team is not registered anywhere should be ignored."""
    _seed(make_user)
    fan = make_user("fan@example.com")
    owner = make_user(
        "other-org@example.com", role=Role.ORGANIZER, display_name="Other Org"
    )
    detached_team = Team(organiser_id=owner.id, name="Detached", short_code="DET")
    db.session.add(detached_team)
    db.session.flush()
    detached_player = Player(
        team_id=detached_team.id,
        name="Detached Player",
        role=PlayerRole.BATTER,
    )
    db.session.add(detached_player)
    db.session.flush()
    db.session.add(
        Follow(
            user_id=fan.id,
            target_type=FollowTarget.PLAYER,
            target_id=detached_player.id,
        )
    )
    db.session.commit()

    login("fan@example.com")
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    # Widget header only renders when at least one followable row survives;
    # the detached player's team has no tournament registration, so the section
    # should not appear.
    assert "Players you follow" not in resp.data.decode()
