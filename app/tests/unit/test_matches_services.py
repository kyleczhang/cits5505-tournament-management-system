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
    Player,
    PlayerRole,
    Role,
    Team,
    TournamentTeam,
    Tournament,
    TournamentFormat,
    TournamentStatus,
    User,
)


def _scaffold(app):
    """Seed an organiser, a 2-team tournament, and a single scheduled match."""
    organiser = User(email="o@example.com", display_name="Org", role=Role.ORGANIZER)
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

    team_a = Team(organiser_id=organiser.id, name="Aces", short_code="ACE")
    team_b = Team(organiser_id=organiser.id, name="Bolts", short_code="BOL")
    db.session.add_all([team_a, team_b])
    db.session.flush()
    entry_a = TournamentTeam(tournament_id=tournament.id, team_id=team_a.id)
    entry_b = TournamentTeam(tournament_id=tournament.id, team_id=team_b.id)
    db.session.add_all([entry_a, entry_b])

    batter = Player(team_id=team_a.id, name="Kyle", role=PlayerRole.BATTER)
    bowler = Player(team_id=team_b.id, name="Max", role=PlayerRole.BOWLER)
    db.session.add_all([batter, bowler])
    db.session.flush()

    match = Match(
        tournament_id=tournament.id,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        scheduled_at=datetime(2026, 4, 2, 14, 0),
    )
    db.session.add(match)
    db.session.commit()
    return organiser, tournament, team_a, team_b, batter, bowler, match


def test_validate_rejects_invalid_winner(app):
    _, _, team_a, team_b, _, _, match = _scaffold(app)
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
    _, _, team_a, _, _, _, match = _scaffold(app)
    payload = {
        "innings": [
            {"batting_team_id": team_a.id, "runs": 100, "wickets": 11, "overs": "20.0"}
        ],
    }
    with pytest.raises(ValidationError) as exc:
        validate_payload(payload, match)
    assert "innings.0.wickets" in exc.value.errors


def test_save_result_marks_match_completed_and_updates_standings(app):
    _, tournament, team_a, team_b, batter, bowler, match = _scaffold(app)
    payload = {
        "result": {"winner_team_id": team_a.id, "result_text": "Aces won by 20 runs"},
        "innings": [
            {
                "batting_team_id": team_a.id,
                "runs": 180,
                "wickets": 6,
                "overs": "20.0",
                "batting": [{"player_id": batter.id, "runs": 45, "balls": 30}],
                "bowling": [
                    {"player_id": bowler.id, "overs": "4.0", "runs": 40, "wickets": 2}
                ],
            },
            {"batting_team_id": team_b.id, "runs": 160, "wickets": 9, "overs": "20.0"},
        ],
    }
    normalised = validate_payload(payload, match)
    save_result(match, normalised)

    db.session.refresh(match)
    db.session.refresh(tournament)
    assert match.status == MatchStatus.COMPLETED
    assert tournament.status == TournamentStatus.COMPLETED
    assert match.winner_id == team_a.id
    assert match.result_text == "Aces won by 20 runs"
    assert len(match.innings) == 2

    entry_a = TournamentTeam.query.filter_by(
        tournament_id=tournament.id, team_id=team_a.id
    ).first()
    entry_b = TournamentTeam.query.filter_by(
        tournament_id=tournament.id, team_id=team_b.id
    ).first()
    assert entry_a.played == 1 and entry_a.won == 1 and entry_a.points == 2
    assert entry_b.played == 1 and entry_b.lost == 1 and entry_b.points == 0
    # NRR: winner's runs-for > runs-against -> positive
    assert Decimal(entry_a.nrr) > 0
    assert Decimal(entry_b.nrr) < 0


def test_save_result_replaces_previous_innings(app):
    _, _, team_a, team_b, _, _, match = _scaffold(app)
    first = validate_payload(
        {
            "result": {"winner_team_id": team_a.id},
            "innings": [
                {
                    "batting_team_id": team_a.id,
                    "runs": 100,
                    "wickets": 8,
                    "overs": "20.0",
                },
                {
                    "batting_team_id": team_b.id,
                    "runs": 90,
                    "wickets": 10,
                    "overs": "18.0",
                },
            ],
        },
        match,
    )
    save_result(match, first)
    assert len(match.innings) == 2

    second = validate_payload(
        {
            "result": {"winner_team_id": team_b.id},
            "innings": [
                {
                    "batting_team_id": team_b.id,
                    "runs": 150,
                    "wickets": 5,
                    "overs": "20.0",
                },
            ],
        },
        match,
    )
    save_result(match, second)
    db.session.refresh(match)
    assert len(match.innings) == 1
    assert match.winner_id == team_b.id


def test_save_result_without_winner_keeps_tournament_live(app):
    _, tournament, team_a, _, _, _, match = _scaffold(app)
    normalised = validate_payload(
        {
            "innings": [
                {
                    "batting_team_id": team_a.id,
                    "runs": 120,
                    "wickets": 4,
                    "overs": "14.0",
                }
            ],
        },
        match,
    )

    save_result(match, normalised)

    db.session.refresh(match)
    db.session.refresh(tournament)
    assert match.status == MatchStatus.LIVE
    assert tournament.status == TournamentStatus.LIVE


def test_validate_rejects_innings_inconsistent_with_toss(app):
    _, _, team_a, team_b, _, _, match = _scaffold(app)
    # Toss winner = A, decision = bowl, so B should bat first. Sending A first
    # should be rejected.
    payload = {
        "toss": {"winner_team_id": team_a.id, "decision": "bowl"},
        "innings": [
            {"batting_team_id": team_a.id, "runs": 100, "wickets": 5, "overs": "20.0"},
            {"batting_team_id": team_b.id, "runs": 90, "wickets": 8, "overs": "20.0"},
        ],
    }
    with pytest.raises(ValidationError) as exc:
        validate_payload(payload, match)
    assert "innings.0.batting_team_id" in exc.value.errors


def test_validate_accepts_innings_consistent_with_toss(app):
    _, _, team_a, team_b, _, _, match = _scaffold(app)
    payload = {
        "toss": {"winner_team_id": team_a.id, "decision": "bowl"},
        "innings": [
            {"batting_team_id": team_b.id, "runs": 90, "wickets": 8, "overs": "20.0"},
            {"batting_team_id": team_a.id, "runs": 100, "wickets": 5, "overs": "20.0"},
        ],
    }
    normalised = validate_payload(payload, match)
    assert normalised["innings"][0]["batting_team_id"] == team_b.id


def test_validate_rejects_player_from_wrong_team(app):
    _, _, team_a, team_b, _, bowler, match = _scaffold(app)
    payload = {
        "innings": [
            {
                "batting_team_id": team_a.id,
                "runs": 100,
                "wickets": 5,
                "overs": "20.0",
                "batting": [{"player_id": bowler.id, "runs": 25, "balls": 20}],
            }
        ]
    }
    with pytest.raises(ValidationError) as exc:
        validate_payload(payload, match)
    assert "innings.0.batting.0.player_id" in exc.value.errors


def test_validate_rejects_invalid_cricket_overs_in_innings(app):
    """Reject overs with invalid decimal (e.g., 10.7 where decimal > 5)."""
    _, _, team_a, _, _, _, match = _scaffold(app)
    payload = {
        "innings": [
            {"batting_team_id": team_a.id, "runs": 100, "wickets": 5, "overs": "10.7"}
        ]
    }
    with pytest.raises(ValidationError) as exc:
        validate_payload(payload, match)
    assert "innings.0.overs" in exc.value.errors


def test_validate_rejects_invalid_cricket_overs_in_bowling(app):
    """Reject bowling overs with invalid decimal (e.g., 19.9 where decimal > 5)."""
    _, _, team_a, team_b, _, bowler, match = _scaffold(app)
    payload = {
        "innings": [
            {
                "batting_team_id": team_a.id,
                "runs": 100,
                "wickets": 5,
                "overs": "20.0",
                "bowling": [
                    {"player_id": bowler.id, "overs": "19.9", "runs": 40, "wickets": 2}
                ],
            }
        ]
    }
    with pytest.raises(ValidationError) as exc:
        validate_payload(payload, match)
    assert "innings.0.bowling.0.overs" in exc.value.errors


def test_validate_accepts_valid_cricket_overs(app):
    """Accept overs in valid cricket format (decimal 0-5)."""
    _, _, team_a, team_b, batter, bowler, match = _scaffold(app)
    payload = {
        "innings": [
            {
                "batting_team_id": team_a.id,
                "runs": 100,
                "wickets": 5,
                "overs": "10.5",
                "batting": [{"player_id": batter.id, "runs": 50, "balls": 40}],
                "bowling": [
                    {"player_id": bowler.id, "overs": "4.3", "runs": 20, "wickets": 1}
                ],
            }
        ]
    }
    normalised = validate_payload(payload, match)
    assert normalised["innings"][0]["overs"] == Decimal("10.5")
    assert normalised["innings"][0]["bowling"][0]["overs"] == Decimal("4.3")


def test_validate_rejects_duplicate_batting_player(app):
    """Reject same player appearing twice in batting entries."""
    _, _, team_a, _, batter, _, match = _scaffold(app)
    payload = {
        "innings": [
            {
                "batting_team_id": team_a.id,
                "runs": 100,
                "wickets": 5,
                "overs": "20.0",
                "batting": [
                    {"player_id": batter.id, "runs": 50, "balls": 40},
                    {"player_id": batter.id, "runs": 30, "balls": 25},
                ],
            }
        ]
    }
    with pytest.raises(ValidationError) as exc:
        validate_payload(payload, match)
    assert "innings.0.batting.1.player_id" in exc.value.errors


def test_validate_rejects_duplicate_bowling_player(app):
    """Reject same player appearing twice in bowling entries."""
    _, _, team_a, team_b, _, bowler, match = _scaffold(app)
    payload = {
        "innings": [
            {
                "batting_team_id": team_a.id,
                "runs": 100,
                "wickets": 5,
                "overs": "20.0",
                "bowling": [
                    {"player_id": bowler.id, "overs": "4.0", "runs": 20, "wickets": 1},
                    {"player_id": bowler.id, "overs": "2.0", "runs": 15, "wickets": 0},
                ],
            }
        ]
    }
    with pytest.raises(ValidationError) as exc:
        validate_payload(payload, match)
    assert "innings.0.bowling.1.player_id" in exc.value.errors


def test_save_result_preserves_legacy_dismissal_on_edit(app):
    """Preserve legacy dismissal values when editing if new value is empty."""
    _, _, team_a, team_b, batter, _, match = _scaffold(app)
    # First save: legacy free-text dismissal (non-standard value)
    first = validate_payload(
        {
            "innings": [
                {
                    "batting_team_id": team_a.id,
                    "runs": 100,
                    "wickets": 1,
                    "overs": "20.0",
                    "batting": [{"player_id": batter.id, "runs": 50, "balls": 40, "dismissal": "Caught behind"}],
                }
            ]
        },
        match,
    )
    save_result(match, first)
    db.session.refresh(match)
    assert match.innings[0].batting_entries[0].dismissal == "Caught behind"

    # Second edit: empty dismissal (user didn't change it) should preserve old value
    second = validate_payload(
        {
            "innings": [
                {
                    "batting_team_id": team_a.id,
                    "runs": 100,
                    "wickets": 1,
                    "overs": "20.0",
                    "batting": [{"player_id": batter.id, "runs": 60, "balls": 45}],
                }
            ]
        },
        match,
    )
    save_result(match, second)
    db.session.refresh(match)
    assert match.innings[0].batting_entries[0].dismissal == "Caught behind"
    assert match.innings[0].batting_entries[0].runs == 60  # runs were updated


def test_validate_rejects_negative_runs_in_batting(app):
    """Reject negative runs in batting entries."""
    _, _, team_a, _, batter, _, match = _scaffold(app)
    payload = {
        "innings": [
            {
                "batting_team_id": team_a.id,
                "runs": 100,
                "wickets": 5,
                "overs": "20.0",
                "batting": [{"player_id": batter.id, "runs": -5, "balls": 10}],
            }
        ]
    }
    with pytest.raises(ValidationError) as exc:
        validate_payload(payload, match)
    assert "innings.0.batting.0.runs" in exc.value.errors


def test_validate_rejects_boundary_runs_exceeding_total(app):
    """Reject when 4s and 6s total more than batter's runs."""
    _, _, team_a, _, batter, _, match = _scaffold(app)
    payload = {
        "innings": [
            {
                "batting_team_id": team_a.id,
                "runs": 100,
                "wickets": 5,
                "overs": "20.0",
                "batting": [
                    {
                        "player_id": batter.id,
                        "runs": 20,
                        "balls": 15,
                        "fours": 8,
                        "sixes": 0,
                    }
                ],
            }
        ]
    }
    with pytest.raises(ValidationError) as exc:
        validate_payload(payload, match)
    assert "innings.0.batting.0.fours" in exc.value.errors


def test_validate_accepts_complete_valid_match_record(app):
    """Accept a complete valid match record with all new validations."""
    _, tournament, team_a, team_b, batter, bowler, match = _scaffold(app)
    payload = {
        "toss": {"winner_team_id": team_a.id, "decision": "bat"},
        "result": {"winner_team_id": team_a.id, "result_text": "Team A won by 10 runs"},
        "innings": [
            {
                "batting_team_id": team_a.id,
                "runs": 150,
                "wickets": 3,
                "overs": "20.0",
                "batting": [
                    {
                        "player_id": batter.id,
                        "runs": 75,
                        "balls": 50,
                        "fours": 8,
                        "sixes": 2,
                        "dismissal": "Not Out",
                    }
                ],
                "bowling": [
                    {
                        "player_id": bowler.id,
                        "overs": "4.2",
                        "maidens": 1,
                        "runs": 25,
                        "wickets": 1,
                    }
                ],
            },
            {
                "batting_team_id": team_b.id,
                "runs": 140,
                "wickets": 8,
                "overs": "20.0",
            },
        ],
    }
    normalised = validate_payload(payload, match)
    save_result(match, normalised)

    db.session.refresh(match)
    assert match.status == MatchStatus.COMPLETED
    assert match.winner_id == team_a.id
    assert len(match.innings) == 2
    assert match.innings[0].batting_entries[0].dismissal == "Not Out"
