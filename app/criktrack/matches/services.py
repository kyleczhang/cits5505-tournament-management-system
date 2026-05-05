"""Validation + persistence helpers for match-result submission."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import (
    BattingEntry,
    BowlingEntry,
    Innings,
    Match,
    MatchStatus,
    Player,
    Team,
    TournamentTeam,
    TossDecision,
)


class ValidationError(Exception):
    """Raised by ``validate_payload`` carrying a {field_path: message} mapping.

    Field paths use dotted notation (e.g. ``innings.0.batting.2.runs``) so the
    frontend can attach error messages to the relevant input.
    """

    def __init__(self, errors: dict[str, str]):
        super().__init__("Validation failed")
        self.errors = errors


def _to_int(
    value: Any, key: str, errors: dict[str, str], min_value: int = 0
) -> int | None:
    try:
        val = int(value)
    except (TypeError, ValueError):
        errors[key] = "Must be a number."
        return None
    if val < min_value:
        errors[key] = f"Must be >= {min_value}."
        return None
    return val


def _to_decimal(value: Any, key: str, errors: dict[str, str]) -> Decimal | None:
    try:
        val = Decimal(str(value))
    except (InvalidOperation, TypeError):
        errors[key] = "Must be a number."
        return None
    if val < 0:
        errors[key] = "Must be >= 0."
        return None
    return val


def validate_payload(payload: dict, match: Match) -> dict:
    """Return a normalised payload or raise ValidationError.

    Validates that toss winner / match winner / batting team are one of the two
    teams that actually played this match, coerces numeric fields, and skips
    blank batting/bowling rows so the form can ship with empty placeholders.
    The returned dict is the contract consumed by ``save_result``.
    """
    errors: dict[str, str] = {}
    if not isinstance(payload, dict):
        raise ValidationError({"_": "Invalid payload."})

    team_ids = {match.team_a_id, match.team_b_id}
    roster_rows = Player.query.filter(Player.team_id.in_(team_ids)).all()
    roster_ids = {
        team_id: {player.id for player in roster_rows if player.team_id == team_id}
        for team_id in team_ids
    }

    toss = payload.get("toss") or {}
    toss_winner = toss.get("winner_team_id")
    toss_decision = toss.get("decision")
    if toss_winner not in (None, ""):
        if int(toss_winner) not in team_ids:
            errors["toss.winner_team_id"] = "Toss winner must be one of the two teams."
        if toss_decision not in ("bat", "bowl"):
            errors["toss.decision"] = "Decision must be 'bat' or 'bowl'."

    result = payload.get("result") or {}
    winner_id = result.get("winner_team_id")
    if winner_id not in (None, ""):
        if int(winner_id) not in team_ids:
            errors["result.winner_team_id"] = "Winner must be one of the two teams."

    raw_innings = payload.get("innings") or []
    if not isinstance(raw_innings, list) or len(raw_innings) == 0:
        errors["innings"] = "At least one innings is required."
        raise ValidationError(errors)

    cleaned_innings = []
    for idx, inn in enumerate(raw_innings):
        prefix = f"innings.{idx}"
        if not isinstance(inn, dict):
            errors[prefix] = "Invalid innings."
            continue
        bat_team = inn.get("batting_team_id")
        try:
            bat_team_id = int(bat_team)
        except (TypeError, ValueError):
            errors[f"{prefix}.batting_team_id"] = "Must select a batting team."
            continue
        if bat_team_id not in team_ids:
            errors[f"{prefix}.batting_team_id"] = (
                "Batting team must be one of the two teams."
            )
            continue
        bowl_team_id = (
            match.team_b_id if bat_team_id == match.team_a_id else match.team_a_id
        )

        runs = _to_int(inn.get("runs", 0), f"{prefix}.runs", errors)
        wickets = _to_int(inn.get("wickets", 0), f"{prefix}.wickets", errors)
        if wickets is not None and wickets > 10:
            errors[f"{prefix}.wickets"] = "Wickets cannot exceed 10."
        overs = _to_decimal(inn.get("overs", 0), f"{prefix}.overs", errors)

        cleaned_batting = []
        for bidx, b in enumerate(inn.get("batting", []) or []):
            bp = f"{prefix}.batting.{bidx}"
            player_id = b.get("player_id")
            if player_id in (None, ""):
                continue
            player_id = _to_int(player_id, f"{bp}.player_id", errors, min_value=1)
            if player_id is None:
                continue
            if player_id not in roster_ids.get(bat_team_id, set()):
                errors[f"{bp}.player_id"] = "Player must belong to the batting team."
                continue
            entry = {
                "player_id": player_id,
                "runs": _to_int(b.get("runs", 0), f"{bp}.runs", errors),
                "balls": _to_int(b.get("balls", 0), f"{bp}.balls", errors),
                "fours": _to_int(b.get("fours", 0), f"{bp}.fours", errors) or 0,
                "sixes": _to_int(b.get("sixes", 0), f"{bp}.sixes", errors) or 0,
                "dismissal": (b.get("dismissal") or "").strip() or None,
                "is_not_out": bool(b.get("is_not_out")),
            }
            cleaned_batting.append(entry)

        cleaned_bowling = []
        for bidx, b in enumerate(inn.get("bowling", []) or []):
            bp = f"{prefix}.bowling.{bidx}"
            player_id = b.get("player_id")
            if player_id in (None, ""):
                continue
            player_id = _to_int(player_id, f"{bp}.player_id", errors, min_value=1)
            if player_id is None:
                continue
            if player_id not in roster_ids.get(bowl_team_id, set()):
                errors[f"{bp}.player_id"] = "Player must belong to the bowling team."
                continue
            entry = {
                "player_id": player_id,
                "overs": _to_decimal(b.get("overs", 0), f"{bp}.overs", errors),
                "maidens": _to_int(b.get("maidens", 0), f"{bp}.maidens", errors) or 0,
                "runs": _to_int(b.get("runs", 0), f"{bp}.runs", errors),
                "wickets": _to_int(b.get("wickets", 0), f"{bp}.wickets", errors),
            }
            cleaned_bowling.append(entry)

        cleaned_innings.append(
            {
                "batting_team_id": bat_team_id,
                "bowling_team_id": bowl_team_id,
                "runs": runs or 0,
                "wickets": wickets or 0,
                "overs": overs or Decimal("0"),
                "batting": cleaned_batting,
                "bowling": cleaned_bowling,
            }
        )

    if errors:
        raise ValidationError(errors)

    return {
        "toss_winner_id": int(toss_winner) if toss_winner not in (None, "") else None,
        "toss_decision": TossDecision(toss_decision)
        if toss_decision in ("bat", "bowl")
        else None,
        "winner_id": int(winner_id) if winner_id not in (None, "") else None,
        "result_text": (result.get("result_text") or "").strip() or None,
        "innings": cleaned_innings,
    }


def save_result(match: Match, normalised: dict) -> Match:
    """Replace the match's innings/entries with the validated payload.

    This is the ONLY supported way to persist a match result. It:

    1. Updates toss/winner/result-text fields on the match.
    2. Wipes existing innings (cascade clears batting/bowling entries) and
       re-inserts fresh rows from the payload.
    3. Calls ``_recompute_standings`` to rebuild every team's
       played/won/lost/points/nrr from scratch.

    Routes must NEVER mutate ``Match.status`` or ``Match.winner_id`` directly:
    bypassing this function will leave tournament standings drifting out of sync.
    """
    match.toss_winner_id = normalised["toss_winner_id"]
    match.toss_decision = normalised["toss_decision"]
    match.winner_id = normalised["winner_id"]
    match.result_text = normalised["result_text"]
    # No winner yet => match is still in progress; once a winner is set it's complete.
    match.status = MatchStatus.COMPLETED if match.winner_id else MatchStatus.LIVE

    # Wipe existing innings (cascade clears batting/bowling entries).
    for inn in list(match.innings):
        db.session.delete(inn)
    db.session.flush()

    for idx, payload in enumerate(normalised["innings"], start=1):
        inn = Innings(
            match_id=match.id,
            inning_number=idx,
            batting_team_id=payload["batting_team_id"],
            bowling_team_id=payload["bowling_team_id"],
            runs=payload["runs"],
            wickets=payload["wickets"],
            overs=payload["overs"],
        )
        db.session.add(inn)
        db.session.flush()

        for b in payload["batting"]:
            player = db.session.get(Player, b["player_id"])
            db.session.add(
                BattingEntry(
                    innings_id=inn.id,
                    player_id=player.id,
                    runs=b["runs"] or 0,
                    balls=b["balls"] or 0,
                    fours=b["fours"],
                    sixes=b["sixes"],
                    dismissal=b["dismissal"],
                    is_not_out=b["is_not_out"],
                )
            )

        for b in payload["bowling"]:
            player = db.session.get(Player, b["player_id"])
            db.session.add(
                BowlingEntry(
                    innings_id=inn.id,
                    player_id=player.id,
                    overs=b["overs"] or Decimal("0"),
                    maidens=b["maidens"],
                    runs=b["runs"] or 0,
                    wickets=b["wickets"] or 0,
                )
            )

    db.session.commit()
    _recompute_standings(match)
    return match


def _recompute_standings(match: Match) -> None:
    """Recalculate played/won/lost/points/nrr for every team in the tournament.

    Rebuilds standings from scratch by iterating all completed matches rather
    than incrementally adjusting — this is the safe default when results can be
    edited or re-recorded, since it avoids accumulated drift from re-saves.
    Points scheme: 2 per win, 0 per loss. NRR = (runs_for/overs_for) -
    (runs_against/overs_against), rounded to two decimals.
    """
    tournament_id = match.tournament_id
    rows = TournamentTeam.query.filter_by(tournament_id=tournament_id).all()
    team_by_id = {row.team_id: row for row in rows}
    # Zero out every team first so deletions/edits can't leave stale totals behind.
    for t in rows:
        t.played = t.won = t.lost = t.points = 0
        t.nrr = 0

    completed = (
        Match.query.options(joinedload(Match.innings))
        .filter_by(tournament_id=tournament_id, status=MatchStatus.COMPLETED)
        .all()
    )

    runs_for: dict[int, Decimal] = {t.team_id: Decimal(0) for t in rows}
    runs_against: dict[int, Decimal] = {t.team_id: Decimal(0) for t in rows}
    overs_for: dict[int, Decimal] = {t.team_id: Decimal(0) for t in rows}
    overs_against: dict[int, Decimal] = {t.team_id: Decimal(0) for t in rows}

    for m in completed:
        if m.team_a_id not in team_by_id or m.team_b_id not in team_by_id:
            continue
        team_by_id[m.team_a_id].played += 1
        team_by_id[m.team_b_id].played += 1
        if m.winner_id and m.winner_id in team_by_id:
            team_by_id[m.winner_id].won += 1
            team_by_id[m.winner_id].points += 2
            loser_id = m.team_b_id if m.winner_id == m.team_a_id else m.team_a_id
            if loser_id in team_by_id:
                team_by_id[loser_id].lost += 1

        for inn in m.innings:
            if inn.batting_team_id in runs_for:
                runs_for[inn.batting_team_id] += Decimal(inn.runs)
                overs_for[inn.batting_team_id] += Decimal(inn.overs)
            if inn.bowling_team_id in runs_against:
                runs_against[inn.bowling_team_id] += Decimal(inn.runs)
                overs_against[inn.bowling_team_id] += Decimal(inn.overs)

    for t in rows:
        rf, of = runs_for[t.team_id], overs_for[t.team_id]
        ra, oa = runs_against[t.team_id], overs_against[t.team_id]
        rf_rate = (rf / of) if of else Decimal(0)
        ra_rate = (ra / oa) if oa else Decimal(0)
        t.nrr = round(float(rf_rate - ra_rate), 2)

    db.session.commit()
