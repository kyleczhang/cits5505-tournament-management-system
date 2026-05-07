"""`flask seed` — load demo fixtures for local development."""

from __future__ import annotations

import click
from flask.cli import with_appcontext

from .extensions import db
from .matches.services import _recompute_standings
from .models import (
    BattingEntry,
    BowlingEntry,
    Comment,
    Innings,
    Match,
    Player,
    Team,
    Tournament,
    TournamentTeam,
    User,
    Venue,
)
from .seed_data import (
    SEED_COMMENTS,
    SEED_ROSTERS,
    SEED_TEAMS,
    SEED_TOURNAMENTS,
    SEED_USERS,
    SEED_VENUES,
)

_DEFAULT_ORGANISER_KEY = "cheng"


def _seed_users() -> dict[str, User]:
    users_by_key: dict[str, User] = {}
    for payload in SEED_USERS:
        user = User(
            email=payload["email"],
            display_name=payload["display_name"],
            role=payload["role"],
            bio=payload.get("bio"),
            location=payload.get("location"),
            avatar_color=payload.get("avatar_color"),
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


def _seed_team_pool(users_by_key: dict[str, User]) -> dict[str, Team]:
    teams_by_name: dict[str, Team] = {}
    organiser_id = users_by_key[_DEFAULT_ORGANISER_KEY].id
    for payload in SEED_TEAMS:
        team = Team(
            organiser_id=organiser_id,
            name=payload["name"],
            short_code=payload["short_code"],
        )
        db.session.add(team)
        teams_by_name[payload["name"]] = team
    db.session.flush()
    return teams_by_name


def _seed_rosters(
    teams_by_name: dict[str, Team],
) -> dict[str, dict[str, Player]]:
    players_by_team: dict[str, dict[str, Player]] = {}
    for team_name, players in SEED_ROSTERS.items():
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


def _roster_player(
    players_by_team: dict[str, dict[str, Player]],
    team: Team,
    player_name: str,
) -> Player:
    """Return a seeded roster player or fail fast if the scorecard is inconsistent."""
    player = players_by_team.get(team.name, {}).get(player_name)
    if player is None:
        raise ValueError(
            f"Seed scorecard references unknown roster player {player_name!r} "
            f"for team {team.name!r}."
        )
    return player


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
            player = _roster_player(players_by_team, batting_team, batting["player_name"])
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
            player = _roster_player(players_by_team, bowling_team, bowling["player_name"])
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
    teams_by_name: dict[str, Team],
    players_by_team: dict[str, dict[str, Player]],
    venues_by_key: dict[str, Venue],
) -> tuple[dict[str, Tournament], dict[str, Match]]:
    tournaments_by_key: dict[str, Tournament] = {}
    matches_by_key: dict[str, Match] = {}

    for payload in SEED_TOURNAMENTS:
        tournament = Tournament(
            name=payload["name"],
            description=payload.get("description"),
            format=payload["format"],
            status=payload["status"],
            start_date=payload["start_date"],
            team_count=len(payload["team_names"]),
            organiser_id=users_by_key[_DEFAULT_ORGANISER_KEY].id,
            venue_id=venues_by_key[payload["venue_key"]].id,
        )
        db.session.add(tournament)
        db.session.flush()
        tournaments_by_key[payload["key"]] = tournament

        for team_name in payload["team_names"]:
            db.session.add(
                TournamentTeam(
                    tournament_id=tournament.id,
                    team_id=teams_by_name[team_name].id,
                )
            )
        db.session.flush()

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

        if tournament.matches:
            _recompute_standings(tournament.matches[0])
            db.session.flush()

    return tournaments_by_key, matches_by_key


def _seed_comments(
    users_by_key: dict[str, User],
    tournaments_by_key: dict[str, Tournament],
    matches_by_key: dict[str, Match],
) -> None:
    for payload in SEED_COMMENTS:
        comment = Comment(
            user_id=users_by_key[payload["user_key"]].id,
            body=payload["body"],
            created_at=payload["created_at"],
        )
        if payload.get("match_key"):
            comment.match_id = matches_by_key[payload["match_key"]].id
        elif payload.get("tournament_key"):
            comment.tournament_id = tournaments_by_key[payload["tournament_key"]].id
        else:
            raise ValueError(
                "Seed comment must reference either match_key or tournament_key."
            )
        db.session.add(comment)


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
    teams_by_name = _seed_team_pool(users_by_key)
    players_by_team = _seed_rosters(teams_by_name)
    tournaments_by_key, matches_by_key = _seed_tournaments(
        users_by_key,
        teams_by_name,
        players_by_team,
        venues_by_key,
    )
    _seed_comments(users_by_key, tournaments_by_key, matches_by_key)

    db.session.commit()
    click.echo(
        f"Seeded {User.query.count()} users, {Team.query.count()} teams, "
        f"{Player.query.count()} players, {Tournament.query.count()} tournaments, "
        f"{Match.query.count()} matches, {Comment.query.count()} comments."
    )
