from __future__ import annotations

from decimal import Decimal

from flask import abort, render_template
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..follows.services import is_following
from ..models import (
    BattingEntry,
    BowlingEntry,
    FollowTarget,
    Innings,
    Match,
    Player,
    Tournament,
)
from . import bp


@bp.route("/tournaments/<int:tournament_id>/players/<int:player_id>")
def stats(tournament_id: int, player_id: int):
    tournament = db.session.get(Tournament, tournament_id) or abort(404)
    player = db.session.get(Player, player_id) or abort(404)
    if player.team is None or player.team.tournament_id != tournament.id:
        abort(404)

    bat_entries = (
        BattingEntry.query.join(Innings, BattingEntry.innings_id == Innings.id)
        .join(Match, Innings.match_id == Match.id)
        .options(joinedload(BattingEntry.innings).joinedload(Innings.match))
        .filter(
            BattingEntry.player_id == player.id,
            Match.tournament_id == tournament.id,
        )
        .all()
    )
    bowl_entries = (
        BowlingEntry.query.join(Innings, BowlingEntry.innings_id == Innings.id)
        .join(Match, Innings.match_id == Match.id)
        .options(joinedload(BowlingEntry.innings).joinedload(Innings.match))
        .filter(
            BowlingEntry.player_id == player.id,
            Match.tournament_id == tournament.id,
        )
        .all()
    )

    total_runs = sum(b.runs for b in bat_entries)
    total_balls = sum(b.balls for b in bat_entries)
    dismissals = sum(1 for b in bat_entries if not b.is_not_out)
    fifties = sum(1 for b in bat_entries if 50 <= b.runs < 100)
    hundreds = sum(1 for b in bat_entries if b.runs >= 100)
    highest = max((b.runs for b in bat_entries), default=0)

    total_wickets = sum(b.wickets for b in bowl_entries)
    total_overs = sum((Decimal(b.overs) for b in bowl_entries), Decimal(0))
    total_conceded = sum(b.runs for b in bowl_entries)

    summary = {
        "matches": len(
            {b.innings.match_id for b in bat_entries}
            | {b.innings.match_id for b in bowl_entries}
        ),
        "runs": total_runs,
        "balls": total_balls,
        "dismissals": dismissals,
        "average": round(total_runs / dismissals, 2) if dismissals else None,
        "strike_rate": round((total_runs / total_balls) * 100, 1)
        if total_balls
        else 0.0,
        "fifties": fifties,
        "hundreds": hundreds,
        "highest": highest,
        "wickets": total_wickets,
        "overs": float(total_overs),
        "economy": round(float(total_conceded) / float(total_overs), 2)
        if total_overs
        else 0.0,
        "bowling_avg": round(total_conceded / total_wickets, 2)
        if total_wickets
        else None,
    }

    matches_played: dict[int, dict] = {}
    for b in bat_entries:
        m = b.innings.match
        matches_played.setdefault(m.id, {"match": m, "bat": None, "bowl": None})
        matches_played[m.id]["bat"] = b
    for b in bowl_entries:
        m = b.innings.match
        matches_played.setdefault(m.id, {"match": m, "bat": None, "bowl": None})
        matches_played[m.id]["bowl"] = b
    history = sorted(
        matches_played.values(),
        key=lambda r: r["match"].scheduled_at,
        reverse=True,
    )

    return render_template(
        "users/player_stats.html",
        tournament=tournament,
        player=player,
        summary=summary,
        history=history,
        is_following_player=is_following(FollowTarget.PLAYER, player.id),
    )
