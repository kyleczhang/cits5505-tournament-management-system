"""`flask seed` — load demo fixtures derived from the frontend's CTM_MOCK."""

from __future__ import annotations

from datetime import UTC, date, datetime

import click
from flask.cli import with_appcontext

from .extensions import db
from .models import (
    BattingEntry,
    BowlingEntry,
    Comment,
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
    User,
    Venue,
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

    organiser = User(
        email="cheng@example.com",
        display_name="Cheng Zhang",
        role=Role.ORGANIZER,
        bio="Club cricketer from Perth. Organiser of the UWA Social League.",
        location="Perth, WA",
    )
    organiser.set_password("password123")

    user = User(
        email="priya@example.com",
        display_name="Priya Menon",
        role=Role.USER,
        bio="Fan of short-format cricket. Follows local WA leagues.",
        location="Perth, WA",
    )
    user.set_password("password123")

    daniel = User(
        email="daniel@example.com",
        display_name="Daniel Park",
        role=Role.USER,
        bio="Off-spinner.",
        location="Perth, WA",
    )
    daniel.set_password("password123")

    db.session.add_all([organiser, user, daniel])
    db.session.flush()

    venue = Venue(
        name="UWA Sports Park",
        address="Hackett Dr, Crawley WA 6009, Australia",
        lat=-31.9833,
        lng=115.8167,
    )
    db.session.add(venue)
    db.session.flush()

    tournament = Tournament(
        name="UWA Social League 2026",
        description="Friendly weekly 20-over matches between UWA clubs.",
        format=TournamentFormat.ROUND_ROBIN,
        status=TournamentStatus.LIVE,
        start_date=date(2026, 3, 15),
        team_count=6,
        organiser_id=organiser.id,
        venue_id=venue.id,
    )
    db.session.add(tournament)
    db.session.flush()

    # A handful more tournaments for the dashboard / list page.
    extras = [
        (
            "Perth Autumn Knockout",
            TournamentFormat.KNOCKOUT,
            TournamentStatus.UPCOMING,
            date(2026, 5, 2),
            8,
        ),
        (
            "Fremantle T20 Cup",
            TournamentFormat.GROUP_STAGE,
            TournamentStatus.COMPLETED,
            date(2025, 11, 10),
            12,
        ),
        (
            "Cottesloe Beach Sixes",
            TournamentFormat.ROUND_ROBIN,
            TournamentStatus.UPCOMING,
            date(2026, 6, 20),
            4,
        ),
        (
            "Nedlands Invitational",
            TournamentFormat.KNOCKOUT,
            TournamentStatus.COMPLETED,
            date(2025, 9, 1),
            8,
        ),
        (
            "Swan Valley Shield",
            TournamentFormat.GROUP_STAGE,
            TournamentStatus.LIVE,
            date(2026, 2, 1),
            10,
        ),
    ]
    for name, fmt, status, sd, tc in extras:
        db.session.add(
            Tournament(
                name=name,
                format=fmt,
                status=status,
                start_date=sd,
                team_count=tc,
                organiser_id=organiser.id,
            )
        )

    teams_seed = [
        ("Crawley Crusaders", "CRU", 5, 5, 0, 10, 2.15),
        ("Nedlands Knights", "NED", 5, 3, 2, 6, 0.82),
        ("Claremont Comets", "CLA", 5, 3, 2, 6, 0.41),
        ("Shenton Sharks", "SHE", 5, 2, 3, 4, -0.30),
        ("Fremantle Falcons", "FRE", 5, 1, 4, 2, -1.25),
        ("Perth Panthers", "PER", 5, 1, 4, 2, -1.84),
    ]
    teams = []
    for name, short, p, w, l, pts, nrr in teams_seed:
        t = Team(
            tournament_id=tournament.id,
            name=name,
            short_code=short,
            played=p,
            won=w,
            lost=l,
            points=pts,
            nrr=nrr,
        )
        db.session.add(t)
        teams.append(t)
    db.session.flush()

    cru, ned, *_rest = teams

    cru_players_seed = [
        ("Aarav Patel", PlayerRole.BATTER),
        ("James Butler", PlayerRole.ALL_ROUNDER),
        ("Ethan Wu", PlayerRole.BATTER),
        ("Noah Smith", PlayerRole.ALL_ROUNDER),
        ("Jacob Lim", PlayerRole.BOWLER),
        ("Arjun Rao", PlayerRole.ALL_ROUNDER),
        ("Daniel Park", PlayerRole.WICKET_KEEPER),
    ]
    ned_players_seed = [
        ("Liam O'Connor", PlayerRole.BATTER),
        ("Ravi Singh", PlayerRole.ALL_ROUNDER),
        ("Sachin Rao", PlayerRole.BOWLER),
        ("Ben Cooper", PlayerRole.BATTER),
        ("Matt Hayes", PlayerRole.BOWLER),
        ("Imran Khan", PlayerRole.BOWLER),
    ]
    cru_players = [Player(team_id=cru.id, name=n, role=r) for n, r in cru_players_seed]
    ned_players = [Player(team_id=ned.id, name=n, role=r) for n, r in ned_players_seed]
    db.session.add_all(cru_players + ned_players)
    db.session.flush()
    cru_by_name = {p.name: p for p in cru_players}
    ned_by_name = {p.name: p for p in ned_players}

    # The completed seed match: Crusaders vs Knights (CTM_MOCK.match #501)
    match = Match(
        tournament_id=tournament.id,
        venue_id=venue.id,
        team_a_id=cru.id,
        team_b_id=ned.id,
        scheduled_at=datetime(2026, 4, 12, 14, 0),
        status=MatchStatus.COMPLETED,
        winner_id=cru.id,
        result_text="Crawley Crusaders won by 17 runs",
    )
    db.session.add(match)
    db.session.flush()

    cru_innings = Innings(
        match_id=match.id,
        inning_number=1,
        batting_team_id=cru.id,
        bowling_team_id=ned.id,
        runs=182,
        wickets=6,
        overs=20.0,
    )
    ned_innings = Innings(
        match_id=match.id,
        inning_number=2,
        batting_team_id=ned.id,
        bowling_team_id=cru.id,
        runs=165,
        wickets=9,
        overs=20.0,
    )
    db.session.add_all([cru_innings, ned_innings])
    db.session.flush()

    cru_batting = [
        ("Aarav Patel", 78, 52, 8, 3, "c Rao b Khan", False),
        ("James Butler", 45, 38, 5, 1, "b Khan", False),
        ("Ethan Wu", 22, 18, 2, 0, "run out", False),
        ("Noah Smith", 14, 9, 1, 1, "c & b Singh", False),
        ("Jacob Lim", 12, 8, 1, 0, "not out", True),
        ("Arjun Rao", 4, 5, 0, 0, "b Khan", False),
        ("Daniel Park", 2, 2, 0, 0, "not out", True),
    ]
    for name, r, b, fours, sixes, dismissal, no in cru_batting:
        db.session.add(
            BattingEntry(
                innings_id=cru_innings.id,
                player_id=cru_by_name[name].id,
                runs=r,
                balls=b,
                fours=fours,
                sixes=sixes,
                dismissal=dismissal,
                is_not_out=no,
            )
        )

    ned_bowling = [
        ("Imran Khan", 4.0, 0, 28, 3),
        ("Ravi Singh", 4.0, 0, 34, 1),
        ("Sachin Rao", 4.0, 0, 41, 0),
        ("Ben Cooper", 4.0, 0, 39, 1),
        ("Matt Hayes", 4.0, 0, 40, 0),
    ]
    for name, ov, m, r, w in ned_bowling:
        db.session.add(
            BowlingEntry(
                innings_id=cru_innings.id,
                player_id=ned_by_name[name].id,
                overs=ov,
                maidens=m,
                runs=r,
                wickets=w,
            )
        )

    ned_batting = [
        ("Liam O'Connor", 62, 44, 6, 2, "c Butler b Park", False),
        ("Ravi Singh", 33, 28, 3, 1, "b Lim", False),
        ("Sachin Rao", 21, 20, 2, 0, "c Wu b Butler", False),
        ("Ben Cooper", 18, 14, 1, 1, "lbw b Lim", False),
        ("Matt Hayes", 10, 11, 1, 0, "c Smith b Butler", False),
        ("Imran Khan", 9, 8, 0, 0, "not out", True),
    ]
    for name, r, b, fours, sixes, dismissal, no in ned_batting:
        db.session.add(
            BattingEntry(
                innings_id=ned_innings.id,
                player_id=ned_by_name[name].id,
                runs=r,
                balls=b,
                fours=fours,
                sixes=sixes,
                dismissal=dismissal,
                is_not_out=no,
            )
        )

    cru_bowling = [
        ("Daniel Park", 4.0, 0, 29, 2),
        ("Jacob Lim", 4.0, 1, 22, 3),
        ("James Butler", 4.0, 0, 34, 2),
        ("Arjun Rao", 4.0, 0, 38, 1),
        ("Noah Smith", 4.0, 0, 42, 1),
    ]
    for name, ov, m, r, w in cru_bowling:
        db.session.add(
            BowlingEntry(
                innings_id=ned_innings.id,
                player_id=cru_by_name[name].id,
                overs=ov,
                maidens=m,
                runs=r,
                wickets=w,
            )
        )

    # Two more (upcoming + live) so the fixtures view has variety.
    db.session.add(
        Match(
            tournament_id=tournament.id,
            venue_id=venue.id,
            team_a_id=teams[0].id,
            team_b_id=teams[2].id,
            scheduled_at=datetime(2026, 4, 21, 18, 30),
            status=MatchStatus.LIVE,
        )
    )
    db.session.add(
        Match(
            tournament_id=tournament.id,
            venue_id=venue.id,
            team_a_id=teams[4].id,
            team_b_id=teams[5].id,
            scheduled_at=datetime(2026, 4, 19, 14, 0),
            status=MatchStatus.UPCOMING,
        )
    )

    # Comments — one organiser, two users.
    db.session.add_all(
        [
            Comment(
                match_id=match.id,
                user_id=organiser.id,
                body="Great hitting from Aarav today — 78 off 52 set the tone.",
                created_at=datetime(2026, 4, 12, 12, 5, tzinfo=UTC),
            ),
            Comment(
                match_id=match.id,
                user_id=user.id,
                body="Knights really needed one more partnership in the middle overs.",
                created_at=datetime(2026, 4, 12, 12, 22, tzinfo=UTC),
            ),
            Comment(
                match_id=match.id,
                user_id=daniel.id,
                body="Pitch was drying out by the second innings — tough to chase 183.",
                created_at=datetime(2026, 4, 13, 0, 41, tzinfo=UTC),
            ),
        ]
    )

    db.session.commit()
    click.echo(
        f"Seeded {User.query.count()} users, {Tournament.query.count()} tournaments, "
        f"{Match.query.count()} matches, {Comment.query.count()} comments."
    )
