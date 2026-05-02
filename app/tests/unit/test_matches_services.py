"""Match-result validation + standings recomputation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest

from criktrack.extensions import db
from criktrack.matches.services import ValidationError, save_result, validate_payload
from criktrack.models import (
    Match,
    MatchStatus,
    Role,
    Team,
    Tournament,
    TournamentFormat,
    TournamentStatus,
    User,
)


def _scaffold(app):
    organiser = User(
        email="o@example.com", display_name="Org", role=Role.ORGANIZER
    )
    organiser.set_password("secret123")
    db.session.add(organiser)
    db.session.flush()

    tournament = Tournament(
        name="T1",
        format=TournamentFormat.ROUND_ROBIN,
        status=TournamentStatus.UPCOMING,
        start_date=date(2026, 4, 1),
        team_count=2,
        organiser_id=organiser.id,
    )
    db.session.add(tournament)
    db.session.flush()

    team_a = Team(tournament_id=tournament.id, name="Aces", short_code="ACE")
    team_b = Team(tournament_id=tournament.id, name="Bolts", short_code="BOL")
    db.session.add_all([team_a, team_b])
    db.session.flush()

    match = Match(
        tournament_id=tournament.id,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        scheduled_at=datetime(2026, 4, 2, 14, 0),
    )
    db.session.add(match)
    db.session.commit()
    return organiser, tournament, team_a, team_b, match


def test_validate_rejects_invalid_winner(app):
    _, _, team_a, team_b, match = _scaffold(app)
    payload = {
        "result": {"winner_team_id": 9999},
        "innings": [
            {"batting_team_id": team_a.id, "runs": 100, "wickets": 5, "overs": "20.0"}
        ],
    }
    with pytest.raises(ValidationError) as exc:
        validate_payload(payload, match)
    assert "result.winner_team_id" in exc.value.errors


def test_validate_rejects_wickets_over_ten(app):
    _, _, team_a, _, match = _scaffold(app)
    payload = {
        "innings": [
            {"batting_team_id": team_a.id, "runs": 100, "wickets": 11, "overs": "20.0"}
        ],
    }
    with pytest.raises(ValidationError) as exc:
        validate_payload(payload, match)
    assert "innings.0.wickets" in exc.value.errors


def test_save_result_marks_match_completed_and_updates_standings(app):
    _, tournament, team_a, team_b, match = _scaffold(app)
    payload = {
        "result": {"winner_team_id": team_a.id, "result_text": "Aces won by 20 runs"},
        "innings": [
            {"batting_team_id": team_a.id, "runs": 180, "wickets": 6, "overs": "20.0",
             "batting": [{"player_name": "Kyle", "runs": 45, "balls": 30}],
             "bowling": [{"player_name": "Max", "overs": "4.0", "runs": 40, "wickets": 2}]},
            {"batting_team_id": team_b.id, "runs": 160, "wickets": 9, "overs": "20.0"},
        ],
    }
    normalised = validate_payload(payload, match)
    save_result(match, normalised)

    db.session.refresh(match)
    assert match.status == MatchStatus.COMPLETED
    assert match.winner_id == team_a.id
    assert match.result_text == "Aces won by 20 runs"
    assert len(match.innings) == 2

    db.session.refresh(team_a)
    db.session.refresh(team_b)
    assert team_a.played == 1 and team_a.won == 1 and team_a.points == 2
    assert team_b.played == 1 and team_b.lost == 1 and team_b.points == 0
    # NRR: winner's runs-for > runs-against -> positive
    assert Decimal(team_a.nrr) > 0
    assert Decimal(team_b.nrr) < 0


def test_save_result_replaces_previous_innings(app):
    _, _, team_a, team_b, match = _scaffold(app)
    first = validate_payload({
        "result": {"winner_team_id": team_a.id},
        "innings": [
            {"batting_team_id": team_a.id, "runs": 100, "wickets": 8, "overs": "20.0"},
            {"batting_team_id": team_b.id, "runs": 90, "wickets": 10, "overs": "18.0"},
        ],
    }, match)
    save_result(match, first)
    assert len(match.innings) == 2

    second = validate_payload({
        "result": {"winner_team_id": team_b.id},
        "innings": [
            {"batting_team_id": team_b.id, "runs": 150, "wickets": 5, "overs": "20.0"},
        ],
    }, match)
    save_result(match, second)
    db.session.refresh(match)
    assert len(match.innings) == 1
    assert match.winner_id == team_b.id
