"""Static demo data consumed by ``flask seed``."""

from __future__ import annotations

from datetime import UTC, date, datetime

from .models import MatchStatus, PlayerRole, Role, TossDecision, TournamentFormat, TournamentStatus

BAT = PlayerRole.BATTER
AR = PlayerRole.ALL_ROUNDER
BWL = PlayerRole.BOWLER
WK = PlayerRole.WICKET_KEEPER


def _player(name: str, role: PlayerRole) -> dict:
    return {"name": name, "role": role}


def _bat(
    player_name: str,
    runs: int,
    balls: int,
    fours: int,
    sixes: int,
    dismissal: str | None = None,
    *,
    is_not_out: bool = False,
) -> dict:
    return {
        "player_name": player_name,
        "runs": runs,
        "balls": balls,
        "fours": fours,
        "sixes": sixes,
        "dismissal": dismissal,
        "is_not_out": is_not_out,
    }


def _bowl(
    player_name: str,
    overs: float,
    maidens: int,
    runs: int,
    wickets: int,
) -> dict:
    return {
        "player_name": player_name,
        "overs": overs,
        "maidens": maidens,
        "runs": runs,
        "wickets": wickets,
    }


def _innings(
    batting_team: str,
    bowling_team: str,
    runs: int,
    wickets: int,
    overs: float,
    *,
    batting: list[dict] | None = None,
    bowling: list[dict] | None = None,
) -> dict:
    payload = {
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "runs": runs,
        "wickets": wickets,
        "overs": overs,
    }
    if batting:
        payload["batting"] = batting
    if bowling:
        payload["bowling"] = bowling
    return payload


SEED_USERS = [
    {
        "key": "cheng",
        "email": "cheng@example.com",
        "display_name": "Cheng Zhang",
        "role": Role.ORGANIZER,
        "bio": "Club cricketer from Perth. Organises local comps and keeps the scorebook tidy.",
        "location": "Perth, WA",
        "avatar_color": "teal",
        "password": "password123",
    },
    {
        "key": "priya",
        "email": "priya@example.com",
        "display_name": "Priya Menon",
        "role": Role.USER,
        "bio": "Follows local T20 cricket and never misses a finals day.",
        "location": "Perth, WA",
        "avatar_color": "violet",
        "password": "password123",
    },
    {
        "key": "daniel",
        "email": "daniel@example.com",
        "display_name": "Daniel Park",
        "role": Role.USER,
        "bio": "Keeper-batter and weekend scorecard nerd.",
        "location": "Perth, WA",
        "avatar_color": "blue",
        "password": "password123",
    },
]

SEED_VENUES = {
    "uwa_sports_park": {
        "name": "UWA Sports Park",
        "address": "Hackett Dr, Crawley WA 6009, Australia",
        "lat": -31.9833,
        "lng": 115.8167,
    },
    "nedlands": {
        "name": "Charles Court Reserve",
        "address": "Brockway Rd, Mount Claremont WA 6010, Australia",
        "lat": -31.9630,
        "lng": 115.7779,
    },
    "fremantle": {
        "name": "Fremantle Community Bank Oval",
        "address": "Parry St, Fremantle WA 6160, Australia",
        "lat": -32.0569,
        "lng": 115.7477,
    },
    "swan_valley": {
        "name": "Lilac Hill Park",
        "address": "Caversham WA 6055, Australia",
        "lat": -31.8693,
        "lng": 115.9737,
    },
    "cottesloe": {
        "name": "Cottesloe Beach Reserve",
        "address": "Marine Parade, Cottesloe WA 6011, Australia",
        "lat": -31.9942,
        "lng": 115.7518,
    },
    "midland": {
        "name": "Harold Rossiter Park",
        "address": "14 Robinson Rd, Middle Swan WA 6056, Australia",
        "lat": -31.8879,
        "lng": 116.0034,
    },
}

SEED_TEAMS = [
    {"name": "Crawley Crusaders", "short_code": "CRU"},
    {"name": "Nedlands Knights", "short_code": "NED"},
    {"name": "Claremont Comets", "short_code": "CLA"},
    {"name": "Shenton Sharks", "short_code": "SHE"},
    {"name": "Fremantle Falcons", "short_code": "FRE"},
    {"name": "Perth Panthers", "short_code": "PER"},
    {"name": "University Aces", "short_code": "UAC"},
    {"name": "Subiaco Strikers", "short_code": "SUB"},
    {"name": "Mount Claremont Kings", "short_code": "MCK"},
    {"name": "Swan Valley Sixers", "short_code": "SVS"},
    {"name": "Cottesloe Chargers", "short_code": "COT"},
    {"name": "Midland Meteors", "short_code": "MID"},
]

SEED_ROSTERS = {
    "Crawley Crusaders": [
        _player("Aarav Patel", BAT),
        _player("Ethan Wu", BAT),
        _player("James Butler", AR),
        _player("Noah Smith", AR),
        _player("Jacob Lim", BWL),
        _player("Daniel Park", WK),
    ],
    "Nedlands Knights": [
        _player("Liam O'Connor", BAT),
        _player("Ben Cooper", BAT),
        _player("Ravi Singh", AR),
        _player("Imran Khan", AR),
        _player("Sachin Rao", BWL),
        _player("Matt Hayes", WK),
    ],
    "Claremont Comets": [
        _player("Oliver Green", BAT),
        _player("Ryan D'Souza", BAT),
        _player("Kieran Moss", AR),
        _player("Zaid Ali", AR),
        _player("Toby Hart", BWL),
        _player("Joel Mercer", WK),
    ],
    "Shenton Sharks": [
        _player("Haris Malik", BAT),
        _player("Sam Nguyen", BAT),
        _player("Dylan Fraser", AR),
        _player("Yusuf Patel", AR),
        _player("Luke Perry", BWL),
        _player("Cooper James", WK),
    ],
    "Fremantle Falcons": [
        _player("Mason Reed", BAT),
        _player("Zane Brooks", BAT),
        _player("Callum Price", AR),
        _player("Vikram Das", AR),
        _player("Aiden Ross", BWL),
        _player("Finn Walker", WK),
    ],
    "Perth Panthers": [
        _player("Isaac Turner", BAT),
        _player("Tyler Young", BAT),
        _player("Kabir Mehta", AR),
        _player("Pranav Iyer", AR),
        _player("Hamish Cole", BWL),
        _player("Joel Francis", WK),
    ],
    "University Aces": [
        _player("Theo Martin", BAT),
        _player("Nathan Cole", BAT),
        _player("Rohan Desai", AR),
        _player("Ben Wallace", AR),
        _player("Marcus Lee", BWL),
        _player("Aiden Clarke", WK),
    ],
    "Subiaco Strikers": [
        _player("Levi Grant", BAT),
        _player("Owen Baxter", BAT),
        _player("Arjun Nair", AR),
        _player("Isaac Dunn", AR),
        _player("Corey Blake", BWL),
        _player("Mason Ford", WK),
    ],
    "Mount Claremont Kings": [
        _player("Hugo Bennett", BAT),
        _player("Caleb Frost", BAT),
        _player("Zayn Merchant", AR),
        _player("Riley Shaw", AR),
        _player("Connor Vale", BWL),
        _player("Jayden Cross", WK),
    ],
    "Swan Valley Sixers": [
        _player("Kian Abbott", BAT),
        _player("Mason Gill", BAT),
        _player("Adil Hussain", AR),
        _player("Cooper Wade", AR),
        _player("Troy Maddox", BWL),
        _player("Ellis Dean", WK),
    ],
    "Cottesloe Chargers": [
        _player("Oscar Pike", BAT),
        _player("Felix Moore", BAT),
        _player("Rishi Kapoor", AR),
        _player("Callan Webb", AR),
        _player("Blake Sutton", BWL),
        _player("Toby Sinclair", WK),
    ],
    "Midland Meteors": [
        _player("Jai Fletcher", BAT),
        _player("Seth Palmer", BAT),
        _player("Nikhil Verma", AR),
        _player("Bailey Kerr", AR),
        _player("Reece Bolton", BWL),
        _player("Devon Marsh", WK),
    ],
}

SEED_TOURNAMENTS = [
    {
        "key": "uwa_social_league",
        "name": "UWA Social League",
        "description": "A compact university round-robin with reusable club squads and weekly scorecards.",
        "format": TournamentFormat.ROUND_ROBIN,
        "status": TournamentStatus.COMPLETED,
        "start_date": date(2026, 3, 15),
        "venue_key": "uwa_sports_park",
        "team_names": [
            "Crawley Crusaders",
            "Nedlands Knights",
            "Claremont Comets",
            "Shenton Sharks",
        ],
        "matches": [
            {
                "key": "uwa-cru-v-ned",
                "team_a": "Crawley Crusaders",
                "team_b": "Nedlands Knights",
                "scheduled_at": datetime(2026, 3, 15, 14, 0),
                "status": MatchStatus.COMPLETED,
                "winner": "Crawley Crusaders",
                "result_text": "Crawley Crusaders won by 9 runs",
                "toss_winner": "Crawley Crusaders",
                "toss_decision": TossDecision.BAT,
                "innings": [
                    _innings(
                        "Crawley Crusaders",
                        "Nedlands Knights",
                        158,
                        5,
                        20.0,
                        batting=[
                            _bat("Aarav Patel", 54, 39, 6, 2, "c Hayes b Khan"),
                            _bat("Ethan Wu", 24, 20, 3, 0, "lbw b Rao"),
                            _bat("James Butler", 37, 27, 4, 1, "b Singh"),
                            _bat("Noah Smith", 16, 13, 1, 0, "c Cooper b Rao"),
                            _bat("Jacob Lim", 9, 7, 1, 0, "run out"),
                            _bat("Daniel Park", 11, 8, 1, 0, is_not_out=True),
                        ],
                        bowling=[
                            _bowl("Ravi Singh", 4.0, 0, 28, 1),
                            _bowl("Sachin Rao", 4.0, 0, 31, 2),
                            _bowl("Imran Khan", 4.0, 0, 33, 1),
                        ],
                    ),
                    _innings(
                        "Nedlands Knights",
                        "Crawley Crusaders",
                        149,
                        8,
                        20.0,
                        batting=[
                            _bat("Liam O'Connor", 48, 36, 5, 1, "c Park b Butler"),
                            _bat("Ben Cooper", 31, 24, 3, 1, "b Lim"),
                            _bat("Ravi Singh", 28, 21, 2, 1, "c Wu b Smith"),
                            _bat("Imran Khan", 14, 10, 1, 0, "c Patel b Lim"),
                            _bat("Matt Hayes", 10, 8, 1, 0, "run out"),
                            _bat("Sachin Rao", 6, 5, 0, 0, is_not_out=True),
                        ],
                        bowling=[
                            _bowl("James Butler", 4.0, 0, 27, 2),
                            _bowl("Jacob Lim", 4.0, 0, 24, 2),
                            _bowl("Noah Smith", 4.0, 0, 30, 1),
                        ],
                    ),
                ],
            },
            {
                "team_a": "Claremont Comets",
                "team_b": "Shenton Sharks",
                "scheduled_at": datetime(2026, 3, 22, 14, 0),
                "status": MatchStatus.COMPLETED,
                "winner": "Claremont Comets",
                "result_text": "Claremont Comets won by 3 runs",
                "innings": [
                    _innings("Claremont Comets", "Shenton Sharks", 141, 7, 20.0),
                    _innings("Shenton Sharks", "Claremont Comets", 138, 9, 20.0),
                ],
            },
            {
                "team_a": "Nedlands Knights",
                "team_b": "Shenton Sharks",
                "scheduled_at": datetime(2026, 3, 29, 14, 0),
                "status": MatchStatus.COMPLETED,
                "winner": "Shenton Sharks",
                "result_text": "Shenton Sharks won by 5 wickets",
                "innings": [
                    _innings("Nedlands Knights", "Shenton Sharks", 135, 8, 20.0),
                    _innings("Shenton Sharks", "Nedlands Knights", 136, 5, 18.4),
                ],
            },
            {
                "team_a": "Crawley Crusaders",
                "team_b": "Claremont Comets",
                "scheduled_at": datetime(2026, 4, 5, 14, 0),
                "status": MatchStatus.COMPLETED,
                "winner": "Crawley Crusaders",
                "result_text": "Crawley Crusaders won by 22 runs",
                "innings": [
                    _innings("Crawley Crusaders", "Claremont Comets", 167, 6, 20.0),
                    _innings("Claremont Comets", "Crawley Crusaders", 145, 9, 20.0),
                ],
            },
        ],
    },
    {
        "key": "nedlands_invitational",
        "name": "Nedlands Invitational",
        "description": "A four-team knockout used to showcase seeded scorecards and player stats.",
        "format": TournamentFormat.KNOCKOUT,
        "status": TournamentStatus.COMPLETED,
        "start_date": date(2026, 2, 8),
        "venue_key": "nedlands",
        "team_names": [
            "University Aces",
            "Subiaco Strikers",
            "Mount Claremont Kings",
            "Perth Panthers",
        ],
        "matches": [
            {
                "team_a": "University Aces",
                "team_b": "Perth Panthers",
                "scheduled_at": datetime(2026, 2, 8, 10, 0),
                "status": MatchStatus.COMPLETED,
                "winner": "University Aces",
                "result_text": "University Aces won by 18 runs",
                "innings": [
                    _innings("University Aces", "Perth Panthers", 152, 7, 20.0),
                    _innings("Perth Panthers", "University Aces", 134, 9, 20.0),
                ],
            },
            {
                "team_a": "Subiaco Strikers",
                "team_b": "Mount Claremont Kings",
                "scheduled_at": datetime(2026, 2, 8, 14, 0),
                "status": MatchStatus.COMPLETED,
                "winner": "Subiaco Strikers",
                "result_text": "Subiaco Strikers won by 6 wickets",
                "innings": [
                    _innings("Mount Claremont Kings", "Subiaco Strikers", 139, 8, 20.0),
                    _innings("Subiaco Strikers", "Mount Claremont Kings", 140, 4, 18.1),
                ],
            },
            {
                "key": "ned-final-uac-v-sub",
                "team_a": "University Aces",
                "team_b": "Subiaco Strikers",
                "scheduled_at": datetime(2026, 2, 15, 15, 0),
                "status": MatchStatus.COMPLETED,
                "winner": "University Aces",
                "result_text": "University Aces won by 4 wickets",
                "toss_winner": "University Aces",
                "toss_decision": TossDecision.BOWL,
                "innings": [
                    _innings(
                        "Subiaco Strikers",
                        "University Aces",
                        147,
                        8,
                        20.0,
                        batting=[
                            _bat("Levi Grant", 41, 33, 4, 1, "c Clarke b Lee"),
                            _bat("Owen Baxter", 26, 21, 2, 1, "b Desai"),
                            _bat("Arjun Nair", 35, 24, 3, 1, "c Martin b Wallace"),
                            _bat("Isaac Dunn", 18, 14, 1, 0, "b Lee"),
                            _bat("Mason Ford", 11, 9, 1, 0, "run out"),
                            _bat("Corey Blake", 7, 6, 0, 0, is_not_out=True),
                        ],
                        bowling=[
                            _bowl("Marcus Lee", 4.0, 0, 25, 2),
                            _bowl("Rohan Desai", 4.0, 0, 29, 1),
                            _bowl("Ben Wallace", 4.0, 0, 30, 1),
                        ],
                    ),
                    _innings(
                        "University Aces",
                        "Subiaco Strikers",
                        148,
                        6,
                        19.1,
                        batting=[
                            _bat("Theo Martin", 46, 35, 5, 1, "c Ford b Blake"),
                            _bat("Nathan Cole", 17, 16, 2, 0, "lbw b Dunn"),
                            _bat("Rohan Desai", 29, 22, 2, 1, "c Grant b Blake"),
                            _bat("Ben Wallace", 21, 17, 2, 0, "b Dunn"),
                            _bat("Aiden Clarke", 14, 11, 1, 0, "run out"),
                            _bat("Marcus Lee", 8, 5, 1, 0, is_not_out=True),
                        ],
                        bowling=[
                            _bowl("Corey Blake", 4.0, 0, 27, 2),
                            _bowl("Isaac Dunn", 4.0, 0, 31, 2),
                            _bowl("Arjun Nair", 3.1, 0, 24, 0),
                        ],
                    ),
                ],
            },
        ],
    },
    {
        "key": "swan_valley_shield",
        "name": "Swan Valley Shield",
        "description": "A live group-stage comp with two early results and one in-progress fixture.",
        "format": TournamentFormat.GROUP_STAGE,
        "status": TournamentStatus.LIVE,
        "start_date": date(2026, 4, 20),
        "venue_key": "swan_valley",
        "team_names": [
            "Swan Valley Sixers",
            "Midland Meteors",
            "Fremantle Falcons",
            "Cottesloe Chargers",
        ],
        "matches": [
            {
                "team_a": "Swan Valley Sixers",
                "team_b": "Midland Meteors",
                "scheduled_at": datetime(2026, 4, 20, 11, 0),
                "status": MatchStatus.COMPLETED,
                "winner": "Swan Valley Sixers",
                "result_text": "Swan Valley Sixers won by 11 runs",
                "innings": [
                    _innings("Swan Valley Sixers", "Midland Meteors", 149, 6, 20.0),
                    _innings("Midland Meteors", "Swan Valley Sixers", 138, 8, 20.0),
                ],
            },
            {
                "team_a": "Fremantle Falcons",
                "team_b": "Cottesloe Chargers",
                "scheduled_at": datetime(2026, 4, 21, 15, 0),
                "status": MatchStatus.COMPLETED,
                "winner": "Fremantle Falcons",
                "result_text": "Fremantle Falcons won by 6 wickets",
                "innings": [
                    _innings("Cottesloe Chargers", "Fremantle Falcons", 131, 9, 20.0),
                    _innings("Fremantle Falcons", "Cottesloe Chargers", 132, 4, 18.2),
                ],
            },
            {
                "key": "svs-live-mid-v-cot",
                "team_a": "Midland Meteors",
                "team_b": "Cottesloe Chargers",
                "scheduled_at": datetime(2026, 4, 27, 14, 0),
                "status": MatchStatus.LIVE,
                "toss_winner": "Cottesloe Chargers",
                "toss_decision": TossDecision.BOWL,
                "innings": [
                    _innings(
                        "Midland Meteors",
                        "Cottesloe Chargers",
                        86,
                        3,
                        11.2,
                        batting=[
                            _bat("Jai Fletcher", 33, 24, 4, 1, "c Sinclair b Kapoor"),
                            _bat("Seth Palmer", 21, 17, 2, 0, "lbw b Sutton"),
                            _bat("Nikhil Verma", 18, 14, 1, 1, "c Pike b Webb"),
                            _bat("Bailey Kerr", 9, 8, 1, 0, is_not_out=True),
                            _bat("Devon Marsh", 3, 4, 0, 0, is_not_out=True),
                        ],
                        bowling=[
                            _bowl("Rishi Kapoor", 3.0, 0, 21, 1),
                            _bowl("Blake Sutton", 3.0, 0, 18, 1),
                            _bowl("Callan Webb", 2.2, 0, 16, 1),
                        ],
                    )
                ],
            },
            {
                "team_a": "Swan Valley Sixers",
                "team_b": "Fremantle Falcons",
                "scheduled_at": datetime(2026, 5, 4, 14, 0),
                "status": MatchStatus.UPCOMING,
            },
        ],
    },
    {
        "key": "harbour_t20_cup",
        "name": "Harbour T20 Cup",
        "description": "A live round-robin comp balancing finished fixtures with one in-progress chase.",
        "format": TournamentFormat.ROUND_ROBIN,
        "status": TournamentStatus.LIVE,
        "start_date": date(2026, 4, 10),
        "venue_key": "fremantle",
        "team_names": [
            "Fremantle Falcons",
            "Perth Panthers",
            "Subiaco Strikers",
            "University Aces",
        ],
        "matches": [
            {
                "key": "harbour-uac-v-fre",
                "team_a": "University Aces",
                "team_b": "Fremantle Falcons",
                "scheduled_at": datetime(2026, 4, 10, 18, 30),
                "status": MatchStatus.COMPLETED,
                "winner": "University Aces",
                "result_text": "University Aces won by 6 runs",
                "toss_winner": "Fremantle Falcons",
                "toss_decision": TossDecision.BOWL,
                "innings": [
                    _innings(
                        "University Aces",
                        "Fremantle Falcons",
                        166,
                        6,
                        20.0,
                        batting=[
                            _bat("Theo Martin", 52, 38, 6, 1, "c Walker b Ross"),
                            _bat("Nathan Cole", 23, 19, 2, 1, "b Das"),
                            _bat("Rohan Desai", 34, 24, 3, 1, "c Reed b Price"),
                            _bat("Ben Wallace", 19, 14, 2, 0, "b Ross"),
                            _bat("Aiden Clarke", 14, 10, 1, 0, is_not_out=True),
                            _bat("Marcus Lee", 8, 5, 1, 0, is_not_out=True),
                        ],
                        bowling=[
                            _bowl("Aiden Ross", 4.0, 0, 30, 2),
                            _bowl("Callum Price", 4.0, 0, 26, 1),
                            _bowl("Vikram Das", 4.0, 0, 32, 1),
                        ],
                    ),
                    _innings(
                        "Fremantle Falcons",
                        "University Aces",
                        160,
                        8,
                        20.0,
                        batting=[
                            _bat("Mason Reed", 44, 34, 5, 1, "c Clarke b Wallace"),
                            _bat("Zane Brooks", 27, 22, 3, 0, "b Lee"),
                            _bat("Callum Price", 31, 23, 2, 1, "c Cole b Desai"),
                            _bat("Vikram Das", 22, 16, 2, 0, "b Wallace"),
                            _bat("Finn Walker", 14, 9, 1, 0, "run out"),
                            _bat("Aiden Ross", 8, 6, 1, 0, is_not_out=True),
                        ],
                        bowling=[
                            _bowl("Ben Wallace", 4.0, 0, 28, 2),
                            _bowl("Marcus Lee", 4.0, 0, 29, 1),
                            _bowl("Rohan Desai", 4.0, 0, 31, 1),
                        ],
                    ),
                ],
            },
            {
                "team_a": "Perth Panthers",
                "team_b": "Subiaco Strikers",
                "scheduled_at": datetime(2026, 4, 13, 18, 30),
                "status": MatchStatus.COMPLETED,
                "winner": "Perth Panthers",
                "result_text": "Perth Panthers won by 5 wickets",
                "innings": [
                    _innings("Subiaco Strikers", "Perth Panthers", 143, 7, 20.0),
                    _innings("Perth Panthers", "Subiaco Strikers", 144, 5, 18.5),
                ],
            },
            {
                "key": "harbour-live-fre-v-per",
                "team_a": "Fremantle Falcons",
                "team_b": "Perth Panthers",
                "scheduled_at": datetime(2026, 4, 18, 16, 0),
                "status": MatchStatus.LIVE,
                "toss_winner": "Perth Panthers",
                "toss_decision": TossDecision.BAT,
                "innings": [
                    _innings(
                        "Perth Panthers",
                        "Fremantle Falcons",
                        72,
                        2,
                        8.4,
                        batting=[
                            _bat("Isaac Turner", 30, 22, 4, 1, "c Walker b Price"),
                            _bat("Tyler Young", 18, 14, 2, 0, "lbw b Ross"),
                            _bat("Kabir Mehta", 15, 10, 1, 1, is_not_out=True),
                            _bat("Joel Francis", 5, 6, 0, 0, is_not_out=True),
                        ],
                        bowling=[
                            _bowl("Callum Price", 2.4, 0, 18, 1),
                            _bowl("Aiden Ross", 3.0, 0, 24, 1),
                        ],
                    )
                ],
            },
            {
                "team_a": "University Aces",
                "team_b": "Subiaco Strikers",
                "scheduled_at": datetime(2026, 4, 24, 18, 30),
                "status": MatchStatus.UPCOMING,
            },
        ],
    },
    {
        "key": "cottesloe_beach_cup",
        "name": "Cottesloe Beach Cup",
        "description": "A short knockout event queued up for one weekend on the coast.",
        "format": TournamentFormat.KNOCKOUT,
        "status": TournamentStatus.UPCOMING,
        "start_date": date(2026, 6, 20),
        "venue_key": "cottesloe",
        "team_names": [
            "Cottesloe Chargers",
            "Claremont Comets",
            "Shenton Sharks",
            "Mount Claremont Kings",
        ],
        "matches": [
            {
                "team_a": "Cottesloe Chargers",
                "team_b": "Shenton Sharks",
                "scheduled_at": datetime(2026, 6, 20, 9, 0),
                "status": MatchStatus.UPCOMING,
            },
            {
                "team_a": "Claremont Comets",
                "team_b": "Mount Claremont Kings",
                "scheduled_at": datetime(2026, 6, 20, 12, 30),
                "status": MatchStatus.UPCOMING,
            },
        ],
    },
    {
        "key": "midland_spring_series",
        "name": "Midland Spring Series",
        "description": "A small group-stage event with reusable squads and a clean upcoming-only fixture list.",
        "format": TournamentFormat.GROUP_STAGE,
        "status": TournamentStatus.UPCOMING,
        "start_date": date(2026, 8, 2),
        "venue_key": "midland",
        "team_names": [
            "Midland Meteors",
            "Crawley Crusaders",
            "Nedlands Knights",
            "Swan Valley Sixers",
        ],
        "matches": [
            {
                "team_a": "Midland Meteors",
                "team_b": "Crawley Crusaders",
                "scheduled_at": datetime(2026, 8, 2, 10, 0),
                "status": MatchStatus.UPCOMING,
            },
            {
                "team_a": "Nedlands Knights",
                "team_b": "Swan Valley Sixers",
                "scheduled_at": datetime(2026, 8, 2, 13, 30),
                "status": MatchStatus.UPCOMING,
            },
            {
                "team_a": "Midland Meteors",
                "team_b": "Swan Valley Sixers",
                "scheduled_at": datetime(2026, 8, 9, 10, 0),
                "status": MatchStatus.UPCOMING,
            },
            {
                "team_a": "Crawley Crusaders",
                "team_b": "Nedlands Knights",
                "scheduled_at": datetime(2026, 8, 9, 13, 30),
                "status": MatchStatus.UPCOMING,
            },
        ],
    },
]

SEED_COMMENTS = [
    {
        "match_key": "uwa-cru-v-ned",
        "user_key": "cheng",
        "body": "Aarav and James gave Crawley exactly the platform they needed here.",
        "created_at": datetime(2026, 3, 15, 8, 25, tzinfo=UTC),
    },
    {
        "match_key": "uwa-cru-v-ned",
        "user_key": "priya",
        "body": "Nedlands stayed in it for a long time, but the chase stalled in the last four overs.",
        "created_at": datetime(2026, 3, 15, 8, 43, tzinfo=UTC),
    },
    {
        "tournament_key": "harbour_t20_cup",
        "user_key": "priya",
        "body": "This tournament has the cleanest mix of finished results and live fixtures in the demo data.",
        "created_at": datetime(2026, 4, 18, 6, 5, tzinfo=UTC),
    },
    {
        "match_key": "svs-live-mid-v-cot",
        "user_key": "daniel",
        "body": "Midland are scoring quickly, but Cottesloe have kept enough wickets in hand on the bowling side.",
        "created_at": datetime(2026, 4, 27, 6, 31, tzinfo=UTC),
    },
    {
        "match_key": "harbour-uac-v-fre",
        "user_key": "daniel",
        "body": "University's middle overs with the bat were the difference in that one.",
        "created_at": datetime(2026, 4, 10, 12, 11, tzinfo=UTC),
    },
]
