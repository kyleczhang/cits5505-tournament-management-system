# CRIKTRACK — Cricket Tournament Management System

A web application for creating and managing cricket tournaments. Organisers can set up fixtures (knockout, round-robin, or group stage), record detailed scorecards, track player statistics, and share tournament results with anyone via a public link.

Built for **CITS5505 (Agile Web Development) — Group Project 2026**.

## Team

| UWA ID   | Name                | GitHub Username |
| -------- | ------------------- | --------------- |
| 24237576 | Hafiz Zeeshan Ahmad | Armaanzee       |
| 24268801 | Leon Nel            | DemionNeo1      |
| 24878502 | Cheng Zhang         | kyleczhang      |

## Status — Checkpoint 3 (Flask backend)

The Flask + SQLAlchemy backend is now wired up end-to-end. All pages are server-rendered from Jinja templates, persistent data lives in SQLite via Flask-Migrate, and the frontend prototype at `frontend-original/` is kept untouched as a design reference.

## Features

- **Organiser-gated tournament creation** — role assigned at sign-up via a secret invite code. Organisers pick a format (round-robin / knockout / group stage), add teams on the fly, attach a venue, and get a shareable public link.
- **Match results + scorecards** — organisers submit full innings (batting + bowling line-ups, toss, winner, result text) through a single JSON-validated form. Scorecards render batting/bowling tables and a venue map for everyone.
- **Live standings** — points, wins/losses, net run rate are recomputed from completed matches after every saved result, so the points table is always consistent.
- **Player stats** — per-player page aggregates batting and bowling across the tournament, showing averages, strike rate, fifties/hundreds, economy, and a match-by-match history.
- **Discussion threads** — logged-in users can comment on any tournament or match via a CSRF-protected JSON API.
- **Live cricket feed** — a dashboard widget pulls currently-live international matches from [cricketdata.org](https://cricketdata.org/) through a server-side proxy with a TTL cache and graceful fallback (live → cache → stale → mock).
- **Venue maps** — addresses are geocoded server-side via Google Maps at venue creation, then rendered client-side (Google when a key is configured, OpenStreetMap otherwise).
- **Public share views** — every tournament gets a `secrets.token_urlsafe` slug that exposes a read-only page with no auth required, ideal for posting in a team chat.
- **Responsive + accessible** — the UI inherits the Checkpoint 2 design system (field-green + championship-gold palette, Bebas Neue display headings, 4.5:1 contrast, skip-to-content link, keyboard focus rings, `prefers-reduced-motion` respected).

## Running the application

All backend code lives under `app/`.

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then edit SECRET_KEY + any API keys
flask --app run:app db upgrade  # create tables from Alembic migrations
flask --app run:app seed        # optional: seed demo data
flask --app run:app run         # serves on http://127.0.0.1:5000
```

### Environment variables

| Variable                        | Purpose                                                    |
| ------------------------------- | ---------------------------------------------------------- |
| `SECRET_KEY`                    | Flask session signing key (set a long random value)        |
| `DATABASE_URL`                  | SQLAlchemy URI (defaults to `sqlite:///criktrack.sqlite3`) |
| `ORGANIZER_INVITE_CODE`         | Sign-up code that promotes a new account to organizer      |
| `GOOGLE_MAPS_API_KEY`           | Optional; client-side Google Maps rendering                |
| `GOOGLE_MAPS_GEOCODING_API_KEY` | Optional; server-side address → lat/lng at venue create    |
| `CRICKETDATA_API_KEY`           | Optional; live match feed from cricketdata.org             |
| `LIVE_FEED_CACHE_SECONDS`       | TTL for the in-process live-feed cache (default 30)        |

When external API keys are absent the app degrades gracefully: maps fall back to OpenStreetMap, the live feed returns an empty `{"status": "mock"}` payload, and geocoding is skipped (venues keep a null lat/lng).

## First-run walkthrough

After `flask run`, a quick smoke test of the main flows:

1. Open <http://127.0.0.1:5000/> and click **Sign up**.
2. Create an account — paste the `ORGANIZER_INVITE_CODE` from your `.env` into the *Organizer invite code* field to get organiser privileges.
3. From the dashboard, click **Create tournament**. Pick a format, add at least two teams, optionally fill in a venue, and submit.
4. On the tournament detail page, open a fixture and click **Enter result** to record a full innings. Submit — you'll be redirected to the scorecard.
5. Click **Share** to copy the public link; open it in a private window to confirm no auth is required.
6. Back on the dashboard, the **Live cricket** widget polls the backend proxy every 30 s. Without a `CRICKETDATA_API_KEY` it shows an empty/mock state.

If you prefer pre-populated data, run `flask --app run:app seed` before step 1 — it creates three demo accounts (all with password `password123`):

- `cheng@example.com` — organiser, owns the *UWA Social League 2026* with six teams and a completed scorecard
- `priya@example.com` — regular user
- `daniel@example.com` — regular user, also a player in one of the teams

Pass `--reset` to wipe and re-seed.

## Running the tests

```bash
cd app
pip install -r requirements-dev.txt
pytest tests/unit          # 20 unit tests
pytest tests/selenium      # 6 end-to-end tests — needs Chrome + chromedriver
pytest                     # all 26
```

The Selenium suite spins up the Flask app on a random port in a background thread and drives a headless Chrome. If Chrome or its driver is unavailable, Selenium tests skip rather than fail.

## Architecture

- **Application factory** (`criktrack/__init__.py`) binds Flask-SQLAlchemy, Flask-Migrate, Flask-Login and Flask-WTF CSRF, then registers one blueprint per feature area.
- **Blueprints:** `auth`, `users`, `tournaments`, `matches`, `players`, `comments` (JSON API), `live` (cricket-feed proxy), `errors`.
- **Role-based access** via a `Role` enum on `User` + a `@require_role("organizer")` decorator.
- **Server-side validation** for match results lives in `matches/services.py`; the record page POSTs JSON and receives per-field errors back.
- **Standings recomputation** runs after every saved match result — played/won/lost/points/NRR are rebuilt from the completed-match set.
- **Comments** are a small JSON REST API under `/api/{matches,tournaments}/<id>/comments`, backed by the same CSRF-protected session cookie.
- **Live cricket feed** is a thin proxy over cricketdata.org with a thread-safe in-process TTL cache and a live → cache → stale → mock fallback chain.
- **Geocoding** calls the Google Maps Geocoding API when a venue is created; a failure/no-key case leaves lat/lng null and the map falls back to OpenStreetMap on the client.

## Security

- Passwords hashed with `pbkdf2:sha256` (600k iterations) via `werkzeug.security`.
- CSRF protection on every form and every JSON POST (`X-CSRFToken` header from JS).
- `Role`-based authorisation, enforced server-side — the client never trusts `current_user.role` for anything sensitive.
- Open-redirect guard on `?next=` — see `_safe_next()` in `auth/routes.py`.
- Response headers set globally: `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: geolocation=(), microphone=(), camera=()`.
- Session cookies are `HttpOnly` + `SameSite=Lax`; `ProdConfig` adds `Secure`.
- User-supplied text is escaped by Jinja by default; comment rendering in JS goes through `escapeHtml()`.
- Secrets (API keys, invite code) live in `.env`, never in the repo — see `.env.example`.

## Key routes

| Method + path                                              | Purpose                                      |
| ---------------------------------------------------------- | -------------------------------------------- |
| `GET /`                                                    | Landing page                                 |
| `GET/POST /register`, `/login`, `POST /logout`             | Auth                                         |
| `GET /dashboard`                                           | Logged-in home                               |
| `GET /tournaments` + `?q=&status=&page=`                   | Search/browse tournaments                    |
| `GET/POST /tournaments/create`                             | Organiser-only                               |
| `GET /tournaments/<id>`                                    | Fixtures, standings, discussion              |
| `GET /tournaments/p/<slug>`                                | Public share view (no auth)                  |
| `GET /tournaments/<tid>/matches/<mid>/scorecard`           | Full scorecard + comments                    |
| `GET/POST /tournaments/<tid>/matches/<mid>/record`         | Organiser-only; POST takes JSON              |
| `GET /tournaments/<tid>/players/<pid>/stats`               | Per-player stats                             |
| `GET/POST /api/matches/<id>/comments`                      | Comments JSON API                            |
| `GET/POST /api/tournaments/<id>/comments`                  | Comments JSON API                            |
| `GET /api/live/matches`                                    | Cricket-feed proxy (cached)                  |

## Project structure

```
.
├── README.md
├── CLAUDE.md                          # Guidance for Claude Code sessions
├── plan-backend.md                    # Checkpoint 3 build plan
├── frontend-original/                 # Checkpoint 2 prototype (untouched)
└── app/
    ├── run.py                         # Flask entrypoint
    ├── config.py                      # Dev / Test / Prod configs
    ├── requirements.txt               # Runtime dependencies
    ├── requirements-dev.txt           # + pytest, selenium
    ├── pytest.ini
    ├── .env.example                   # Copy to .env
    ├── migrations/                    # Alembic
    ├── criktrack/
    │   ├── __init__.py                # App factory
    │   ├── extensions.py              # db, migrate, login_manager, csrf
    │   ├── decorators.py              # @require_role
    │   ├── filters.py                 # pretty_date, etc.
    │   ├── seed.py                    # `flask seed` CLI
    │   ├── models/                    # User, Tournament, Team, Match, …
    │   ├── auth/ users/ tournaments/  # Feature blueprints
    │   ├── matches/ players/ comments/
    │   ├── live/                      # /api/live/matches proxy
    │   ├── integrations/              # cricketdata + geocoding clients
    │   ├── templates/                 # Server-rendered Jinja
    │   └── static/                    # CSS + JS (record, comments, maps, livefeed)
    └── tests/
        ├── conftest.py
        ├── unit/                      # 20 pytest tests
        └── selenium/                  # 6 end-to-end tests
```

## Team organisation

- **Meetings:** Every Wednesday 12 PM – 2 PM, adjusted via When2Meet when needed.
- **Communication:** Microsoft Teams for day-to-day discussion; GitHub Issues and Pull Requests for task tracking and code review.
- **Workflow:** Each feature or bug fix is developed on its own branch and merged via Pull Request with at least one review from another team member.

### Checkpoint 3 — backend task allocation

| Member              | Area                                                                                   |
| ------------------- | -------------------------------------------------------------------------------------- |
| Hafiz Zeeshan Ahmad | Auth blueprint, users/profile, landing + dashboard, search & public tournament views   |
| Leon Nel            | Tournaments blueprint, create-tournament flow, match record form, standings service    |
| Cheng Zhang         | Match scorecard, player stats, comments API, live-feed proxy, geocoding, test harness  |
