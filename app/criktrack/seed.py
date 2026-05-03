"""`flask seed` — load demo fixtures for local development."""

from __future__ import annotations

import click
from flask.cli import with_appcontext

from .extensions import db
from .models import (
    BattingEntry,
    BowlingEntry,
    Comment,
    Innings,
    Match,
    Player,
    PlayerRole,
    Team,
    Tournament,
    User,
    Venue,
)
from .seed_data import SEED_COMMENTS, SEED_TOURNAMENTS, SEED_USERS, SEED_VENUES

_DEFAULT_ORGANISER_KEY = "cheng"


def _team_short_code(name: str) -> str:
    cleaned = "".join(c for c in name.upper() if c.isalpha())
    return (cleaned[:3] or "TBD")[:4]


def _seed_users() -> dict[str, User]:
    users_by_key: dict[str, User] = {}
    for payload in SEED_USERS:
        user = User(
            email=payload["email"],
            display_name=payload["display_name"],
            role=payload["role"],
            bio=payload.get("bio"),
            location=payload.get("location"),
        )
        user.set_password(payload["password"])
        db.session.add(user)
        users_by_key[payload["key"]] = user
    db.session.flush()
    return users_by_key


def _seed_venues() -> dict[str, Venue]:
    venues_by_key: dict[str, Venue] = {}
    for key, payload in SEED_VENUES.items():
        venue = Venue(**payload)
        db.session.add(venue)
        venues_by_key[key] = venue
    db.session.flush()
    return venues_by_key


def _seed_teams(
    tournament: Tournament,
    team_rows: list[dict],
) -> dict[str, Team]:
    teams_by_name: dict[str, Team] = {}
    for row in team_rows:
        team = Team(
            tournament_id=tournament.id,
            name=row["name"],
            short_code=row.get("short_code") or _team_short_code(row["name"]),
            played=row["played"],
            won=row["won"],
            lost=row["lost"],
            points=row["points"],
            nrr=row["nrr"],
        )
        db.session.add(team)
        teams_by_name[row["name"]] = team
    db.session.flush()
    return teams_by_name


def _ensure_player(
    players_by_team: dict[str, dict[str, Player]],
    team: Team,
    player_name: str,
) -> Player:
    team_players = players_by_team.setdefault(team.name, {})
    existing = team_players.get(player_name)
    if existing is not None:
        return existing

    player = Player(team_id=team.id, name=player_name, role=PlayerRole.ALL_ROUNDER)
    db.session.add(player)
    db.session.flush()
    team_players[player_name] = player
    return player


def _seed_rosters(
    roster_data: dict[str, list[dict]],
    teams_by_name: dict[str, Team],
) -> dict[str, dict[str, Player]]:
    players_by_team: dict[str, dict[str, Player]] = {}
    for team_name, players in roster_data.items():
        team = teams_by_name[team_name]
        players_by_name: dict[str, Player] = {}
        for payload in players:
            player = Player(
                team_id=team.id,
                name=payload["name"],
                role=payload["role"],
            )
            db.session.add(player)
            players_by_name[payload["name"]] = player
        players_by_team[team_name] = players_by_name
    db.session.flush()
    return players_by_team


def _seed_match(
    tournament: Tournament,
    match_data: dict,
    teams_by_name: dict[str, Team],
    players_by_team: dict[str, dict[str, Player]],
    venues_by_key: dict[str, Venue],
) -> Match:
    team_a = teams_by_name[match_data["team_a"]]
    team_b = teams_by_name[match_data["team_b"]]
    venue = venues_by_key.get(match_data.get("venue_key")) or tournament.venue
    winner = (
        teams_by_name.get(match_data["winner"]) if match_data.get("winner") else None
    )
    toss_winner = (
        teams_by_name.get(match_data["toss_winner"])
        if match_data.get("toss_winner")
        else None
    )

    match = Match(
        tournament_id=tournament.id,
        venue_id=venue.id if venue else None,
        team_a_id=team_a.id,
        team_b_id=team_b.id,
        scheduled_at=match_data["scheduled_at"],
        status=match_data["status"],
        winner_id=winner.id if winner else None,
        result_text=match_data.get("result_text"),
        toss_winner_id=toss_winner.id if toss_winner else None,
        toss_decision=match_data.get("toss_decision"),
    )
    db.session.add(match)
    db.session.flush()

    for idx, innings_data in enumerate(match_data.get("innings", []), start=1):
        batting_team = teams_by_name[innings_data["batting_team"]]
        bowling_team = teams_by_name[innings_data["bowling_team"]]
        innings = Innings(
            match_id=match.id,
            inning_number=idx,
            batting_team_id=batting_team.id,
            bowling_team_id=bowling_team.id,
            runs=innings_data["runs"],
            wickets=innings_data["wickets"],
            overs=innings_data["overs"],
        )
        db.session.add(innings)
        db.session.flush()

        for batting in innings_data.get("batting", []):
            player = _ensure_player(
                players_by_team, batting_team, batting["player_name"]
            )
            db.session.add(
                BattingEntry(
                    innings_id=innings.id,
                    player_id=player.id,
                    runs=batting["runs"],
                    balls=batting["balls"],
                    fours=batting["fours"],
                    sixes=batting["sixes"],
                    dismissal=batting["dismissal"],
                    is_not_out=batting["is_not_out"],
                )
            )

        for bowling in innings_data.get("bowling", []):
            player = _ensure_player(
                players_by_team, bowling_team, bowling["player_name"]
            )
            db.session.add(
                BowlingEntry(
                    innings_id=innings.id,
                    player_id=player.id,
                    overs=bowling["overs"],
                    maidens=bowling["maidens"],
                    runs=bowling["runs"],
                    wickets=bowling["wickets"],
                )
            )

    db.session.flush()
    return match


def _seed_tournaments(
    users_by_key: dict[str, User],
    venues_by_key: dict[str, Venue],
) -> dict[str, Match]:
    matches_by_key: dict[str, Match] = {}

    for payload in SEED_TOURNAMENTS:
        tournament = Tournament(
            name=payload["name"],
            description=payload.get("description"),
            format=payload["format"],
            status=payload["status"],
            start_date=payload["start_date"],
            team_count=payload["team_count"],
            organiser_id=users_by_key[_DEFAULT_ORGANISER_KEY].id,
            venue_id=venues_by_key[payload["venue_key"]].id,
        )
        db.session.add(tournament)
        db.session.flush()

        teams_by_name = _seed_teams(tournament, payload["teams"])
        players_by_team = _seed_rosters(payload.get("rosters", {}), teams_by_name)

        for match_payload in payload.get("matches", []):
            match = _seed_match(
                tournament,
                match_payload,
                teams_by_name,
                players_by_team,
                venues_by_key,
            )
            if match_payload.get("key"):
                matches_by_key[match_payload["key"]] = match

    return matches_by_key


def _seed_comments(
    users_by_key: dict[str, User],
    matches_by_key: dict[str, Match],
) -> None:
    for payload in SEED_COMMENTS:
        db.session.add(
            Comment(
                match_id=matches_by_key[payload["match_key"]].id,
                user_id=users_by_key[payload["user_key"]].id,
                body=payload["body"],
                created_at=payload["created_at"],
            )
        )


@click.command("seed")
@click.option("--reset", is_flag=True, help="Wipe existing data first.")
@with_appcontext
def seed_cli(reset: bool):
    """Load demo fixtures into the database."""
    if reset:
        click.echo("Resetting tables...")
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

    if User.query.count() > 0 and not reset:
        click.echo("Already seeded — pass --reset to re-seed.")
        return

    users_by_key = _seed_users()
    venues_by_key = _seed_venues()
    matches_by_key = _seed_tournaments(users_by_key, venues_by_key)
    _seed_comments(users_by_key, matches_by_key)

    db.session.commit()
    click.echo(
        f"Seeded {User.query.count()} users, {Tournament.query.count()} tournaments, "
        f"{Match.query.count()} matches, {Comment.query.count()} comments."
    )
