# CRIKTRACK

CRIKTRACK is a Flask + SQLAlchemy cricket tournament management system built for **CITS5505 Agile Web Development**. It supports organiser-managed tournaments, reusable teams and rosters, detailed match scorecards, public sharing, fan-facing dashboards, comments, follows, and a cached live cricket feed.

All active application code lives in [`app/`](app/). Project documentation, design notes, setup guides, and historical reference material live under [`docs/`](docs/).

## Team

| UWA ID   | Name                | GitHub Username |
| -------- | ------------------- | --------------- |
| 24237576 | Hafiz Zeeshan Ahmad | Armaanzee       |
| 24268801 | Leon Nel            | DemionNeo1      |
| 24878502 | Cheng Zhang         | kyleczhang      |

## What the app does

- Organisers can create tournaments in round-robin, knockout, or group-stage formats.
- Teams are reusable across tournaments and each team has its own editable roster.
- Match scheduling, live/in-progress state, and result recording are handled in the Flask app.
- Scorecards store innings, batting, bowling, toss, winner, and standings-impacting result data.
- Tournament standings are recomputed from recorded completed matches after every saved result.
- Fans can browse live and upcoming tournaments, recent results, profiles, and public share pages.
- Logged-in users can comment on matches and tournaments, and follow tournaments, teams, and players.
- Venue maps use Google Maps when configured and fall back to OpenStreetMap otherwise.
- A live-match widget proxies CricAPI's `currentMatches` endpoint with in-process caching and stale/mock fallback.

## Current architecture

- **App factory:** [`app/criktrack/__init__.py`](app/criktrack/__init__.py)
- **Templates:** [`app/criktrack/templates/`](app/criktrack/templates/)
- **Static assets:** [`app/criktrack/static/`](app/criktrack/static/)
- **Tests:** [`app/tests/`](app/tests/)
- **Database migrations:** [`app/migrations/`](app/migrations/)

Registered blueprints:

- `auth` for registration and login
- `users` for dashboards and profiles
- `teams` for organiser-owned team and roster management
- `tournaments` for tournament list, create, detail, and public share view
- `matches` for fixture creation, start, result recording, and scorecards
- `players` for per-tournament player stats
- `comments` for JSON comment endpoints
- `follows` for JSON follow/unfollow endpoints
- `live` for the live cricket proxy
- `errors` for error pages

## Quick start

### Option 1: manual setup

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
flask --app run:app db upgrade
flask --app run:app seed          # optional
flask --app run:app run
```

The development server runs on `http://127.0.0.1:5000`.

### Option 2: using `make`

```bash
cd app
make setup-dev
make seed              # optional
make run
```

`make setup-dev` creates `.venv`, installs development dependencies, bootstraps `.env` if missing, and runs `db upgrade`.

## Environment variables

The backend reads configuration from [`app/.env`](app/.env) via [`app/config.py`](app/config.py).

| Variable | Purpose |
| -------- | ------- |
| `SECRET_KEY` | Required. Signs session cookies and CSRF tokens. |
| `DATABASE_URL` | SQLAlchemy database URL. Defaults to `sqlite:///criktrack.sqlite3`. |
| `ORGANIZER_INVITE_CODE` | Secret code that grants organiser role during registration. |
| `GOOGLE_MAPS_API_KEY` | Optional. Enables Google Maps rendering on the client. |
| `GOOGLE_MAPS_GEOCODING_API_KEY` | Optional. Enables server-side venue geocoding. |
| `CRICKETDATA_API_KEY` | Optional. Enables live cricket data fetches from CricAPI. |
| `LIVE_FEED_CACHE_SECONDS` | TTL for the in-process live-feed cache. |
| `LIVE_FEED_POLL_MS` | Frontend polling interval for the live widget. |

`SECRET_KEY` is mandatory. The app fails fast at startup if it is missing.

When external API keys are not configured:

- venue pages fall back to OpenStreetMap embeds
- geocoding is skipped and venues keep null coordinates
- the live feed returns mock or empty fallback data instead of failing the page

Setup guides:

- [`docs/api-key-setup/google-maps-setup-en.md`](docs/api-key-setup/google-maps-setup-en.md)
- [`docs/api-key-setup/cricketdata-setup-en.md`](docs/api-key-setup/cricketdata-setup-en.md)

## Demo data

Run:

```bash
cd app
flask --app run:app seed
```

Or reset and reseed:

```bash
cd app
flask --app run:app seed --reset
```

The seed command creates:

- 3 demo users, all with password `password123`
- 12 reusable teams with rosters
- 6 venues
- multiple tournaments across `upcoming`, `live`, and `completed` states
- seeded matches, scorecards, and comments

Demo accounts:

- `cheng@example.com` — organizer account
- `priya@example.com` — general user account
- `daniel@example.com` — general user account

Use password `password123` for all three accounts.

Recommended test logins:

- Organizer flow: `cheng@example.com`
- General user flow: `priya@example.com` or `daniel@example.com`

## Testing

From [`app/`](app/):

```bash
cd app
```

Manual commands:

```bash
.venv/bin/python -m pytest tests -q
.venv/bin/python -m pytest tests/unit -q
.venv/bin/python -m pytest tests/selenium -q
```

Equivalent `make` targets:

```bash
make test
make test-unit
make test-selenium
```

Current baseline from this repository:

- On a fully provisioned local machine: `86 passed` with `.venv/bin/python -m pytest tests -q`

Notes:

- Selenium tests start a live Flask server with a file-backed SQLite database.
- `TestConfig` disables CSRF to keep form and JSON endpoint tests straightforward.

## Main user flows

### Organiser flow

1. Register with the organiser invite code.
2. Create reusable teams and add roster players.
3. Create a tournament and register teams into it.
4. Schedule fixtures, start a match, and record innings-based results.
5. Share the public tournament page with anyone.

### Fan flow

1. Register or log in as a normal user.
2. Browse live and upcoming tournaments from the dashboard.
3. Open scorecards, player stats, and tournament pages.
4. Follow tournaments, teams, or players.
5. Post comments on matches and tournaments.

## Key routes

| Method + path | Purpose |
| ------------- | ------- |
| `GET /` | Landing page |
| `GET/POST /register`, `GET/POST /login`, `POST /logout` | Authentication |
| `GET /dashboard` | Role-aware dashboard |
| `GET /teams` | Organiser team list |
| `GET/POST /teams/create` | Create team |
| `GET /teams/<team_id>` | Team detail and roster tools |
| `GET /tournaments` | Tournament list and filters |
| `GET/POST /tournaments/create` | Create tournament |
| `GET /tournaments/<tournament_id>` | Tournament detail |
| `GET /tournaments/<slug>/share` | Anonymous public share view |
| `GET/POST /tournaments/<tournament_id>/matches/create` | Create fixture |
| `POST /tournaments/<tournament_id>/matches/<match_id>/start` | Mark a match live |
| `GET /tournaments/<tournament_id>/matches/<match_id>` | Scorecard |
| `GET/POST /tournaments/<tournament_id>/matches/<match_id>/record` | Record result; JSON POST |
| `GET /tournaments/<tournament_id>/players/<player_id>` | Player stats |
| `GET/POST /api/matches/<id>/comments` | Match comments JSON API |
| `GET/POST /api/tournaments/<id>/comments` | Tournament comments JSON API |
| `POST /api/follow`, `DELETE /api/follow` | Follow or unfollow target |
| `GET /api/follow/status` | Follow status check |
| `GET /api/live/matches` | Cached live cricket proxy |

## Project structure

```text
.
├── README.md
├── docs/
│   ├── api-key-setup/
│   ├── checkpoint-2/
│   ├── design-doc/
│   │   ├── database-design-v1.md
│   │   ├── implementation-plan-v2.md
│   │   ├── plan-backend-v1.md
│   │   ├── plan-frontend-v1.md
│   │   └── product-v2.md
│   └── project-description-and-rubrics.md
└── app/
    ├── Makefile
    ├── run.py
    ├── wsgi.py
    ├── config.py
    ├── requirements.txt
    ├── requirements-dev.txt
    ├── .env.example
    ├── migrations/
    ├── criktrack/
    │   ├── __init__.py
    │   ├── auth/
    │   ├── comments/
    │   ├── follows/
    │   ├── integrations/
    │   ├── live/
    │   ├── matches/
    │   ├── models/
    │   ├── players/
    │   ├── static/
    │   ├── teams/
    │   ├── templates/
    │   ├── tournaments/
    │   └── users/
    └── tests/
        ├── selenium/
        └── unit/
```

## Development notes

- Work from [`app/`](app/) for nearly all development commands.
- `docs/checkpoint-2/` is a historical static prototype. Use it as reference material, not an active edit target.
- JSON POST endpoints expect the `X-CSRFToken` header from the browser.
- Match results should go through `matches/services.py` so standings stay consistent.
- The public share page is intentionally anonymous-friendly.
- The live-feed cache is single-process and in-memory; it is sufficient for local/dev use.

## Further reading

- [`docs/design-doc/product-v2.md`](docs/design-doc/product-v2.md)
- [`docs/design-doc/implementation-plan-v2.md`](docs/design-doc/implementation-plan-v2.md)
- [`docs/design-doc/database-design-v1.md`](docs/design-doc/database-design-v1.md)
- [`docs/project-description-and-rubrics.md`](docs/project-description-and-rubrics.md)
