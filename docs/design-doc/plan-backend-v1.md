# Backend Implementation Plan — Checkpoint 3

This document is the design and implementation plan for the **Flask backend** of CRIKTRACK (Cricket Tournament Management System). It expands [frontend-original/IMPLEMENTATION-PLAN.md](frontend-original/IMPLEMENTATION-PLAN.md) §12–§16 (the "Backend Integration Contract") into concrete, actionable engineering work, and maps every requirement from [checkpoint-2-doc.md](checkpoint-2-doc.md) and [project-description-and-rubrics.md](project-description-and-rubrics.md) to a code artefact.

The shipped Checkpoint 2 prototype in [frontend-original/](frontend-original/) is treated as the source of truth for HTML/CSS/JS and the data shapes it expects. The backend's job is to honour those contracts so `css/styles.css`, `js/main.js`, `js/maps.js`, `js/comments.js`, `js/livefeed.js` and every `<main>` block can drop into Jinja templates without modification.

---

## 1. Goals

1. Deliver a fully working Flask application meeting every "Overall Application" rubric line in [project-description-and-rubrics.md](project-description-and-rubrics.md).
2. Honour the contracts in [frontend-original/IMPLEMENTATION-PLAN.md](frontend-original/IMPLEMENTATION-PLAN.md) §16 so frontend assets are reused untouched.
3. Implement all 13 user-stories in [checkpoint-2-doc.md](checkpoint-2-doc.md) §2.
4. Ship 5+ pytest unit tests and 5+ Selenium tests against a live server.
5. Be runnable by a teammate in two commands: `pip install -r requirements.txt && flask run` (after `cp .env.example .env`).

---

## 2. Tech Stack

| Concern              | Choice                                                                |
| -------------------- | --------------------------------------------------------------------- |
| Language / runtime   | Python 3.11+                                                          |
| Web framework        | Flask 3.x                                                             |
| Templating           | Jinja2 (bundled with Flask)                                           |
| ORM                  | Flask-SQLAlchemy 3.x (SQLAlchemy 2.x style)                           |
| Migrations           | Flask-Migrate (Alembic) — required by rubric "evidence of migrations" |
| Auth sessions        | Flask-Login                                                           |
| Forms / CSRF         | Flask-WTF (WTForms)                                                   |
| Password hashing     | `werkzeug.security` (PBKDF2-SHA256 with per-user salt)                |
| Config / secrets     | `python-dotenv` + `os.environ`                                        |
| HTTP client (proxy)  | `requests`                                                            |
| Caching (live feed)  | In-process TTL dict (no extra dep); upgrade path: `Flask-Caching`     |
| Database             | SQLite (dev + tests); file at `instance/criktrack.sqlite3`            |
| Test runner          | pytest + pytest-flask                                                 |
| Browser tests        | Selenium 4 + webdriver-manager + ChromeDriver                         |
| Package manager      | pip + venv (`requirements.txt`, optional `requirements-dev.txt`)      |

No build step, no Node, no compiled assets. The frontend is shipped verbatim from [frontend-original/](frontend-original/).

---

## 3. Project Structure

Final tree under [app/](app/) (the new backend root). Files marked `*` are created in this checkpoint; everything else either copies from [frontend-original/](frontend-original/) or comes from running `flask db init`.

```
app/
├── run.py                       # entry point (`flask --app run:app run`) *
├── wsgi.py                      # production WSGI shim (gunicorn target) *
├── config.py                    # Config / DevConfig / TestConfig classes *
├── requirements.txt             # runtime deps *
├── requirements-dev.txt         # pytest, selenium, webdriver-manager, etc. *
├── .env.example                 # env var template (no secrets) *
├── .gitignore                   # ignores .env, instance/, __pycache__, etc. *
├── README.md                    # short backend-specific run + test guide *
├── instance/                    # auto-created; holds SQLite DB and prod-only config
│
├── criktrack/                   # the importable Flask package
│   ├── __init__.py              # create_app() factory; extension binding *
│   ├── extensions.py            # db, migrate, login_manager, csrf singletons *
│   ├── decorators.py            # @require_role('organizer'), JSON error wrapper *
│   ├── seed.py                  # `flask seed` CLI — loads CTM_MOCK fixtures *
│   ├── filters.py               # Jinja filters: relative_time, initials, etc. *
│   │
│   ├── models/                  # one model per file for readability
│   │   ├── __init__.py          # re-exports for convenient imports
│   │   ├── user.py              # User + Role enum
│   │   ├── tournament.py        # Tournament, Team, TeamMembership
│   │   ├── player.py            # Player
│   │   ├── match.py             # Match, Innings, BattingEntry, BowlingEntry
│   │   ├── venue.py             # Venue
│   │   └── comment.py           # Comment
│   │
│   ├── auth/                    # blueprint: /register /login /logout
│   │   ├── __init__.py          # bp = Blueprint('auth', ...)
│   │   ├── routes.py
│   │   └── forms.py             # RegisterForm, LoginForm
│   │
│   ├── tournaments/             # blueprint: /tournaments/*
│   │   ├── __init__.py
│   │   ├── routes.py            # list, create, detail, public-share
│   │   ├── forms.py             # TournamentForm, TeamForm
│   │   └── services.py          # fixture generation, points-table, NRR
│   │
│   ├── matches/                 # blueprint: /tournaments/<id>/matches/*
│   │   ├── __init__.py
│   │   ├── routes.py            # scorecard view, record (GET/POST AJAX)
│   │   ├── forms.py             # MatchResultForm (or schema-only if pure JSON)
│   │   └── services.py          # apply_match_result(), recompute aggregates
│   │
│   ├── players/                 # blueprint: /tournaments/<id>/players/<pid>
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── services.py          # per-tournament player aggregates
│   │
│   ├── users/                   # blueprint: /users/<id>, /profile/edit, /dashboard
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py             # ProfileEditForm
│   │
│   ├── comments/                # blueprint: /api/{matches|tournaments}/<id>/comments
│   │   ├── __init__.py
│   │   ├── routes.py            # GET list, POST create (JSON, CSRF-protected)
│   │   └── schemas.py           # to_dict() helpers matching §16.5 contract
│   │
│   ├── live/                    # blueprint: /api/live/matches
│   │   ├── __init__.py
│   │   ├── routes.py            # JSON proxy
│   │   └── client.py            # CricketDataClient with 30s TTL cache
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── geocoding.py         # Google Maps Geocoding (server-side, on create)
│   │
│   ├── errors/
│   │   ├── __init__.py
│   │   └── handlers.py          # 400/401/403/404/500 -> error.html or JSON
│   │
│   ├── templates/
│   │   ├── base.html            # injects nav + footer partials, CTM_CONFIG, CSRF meta
│   │   ├── partials/
│   │   │   ├── nav.html
│   │   │   ├── footer.html
│   │   │   ├── role_switcher.html      # dev-only, gated on FLASK_ENV
│   │   │   └── flash_messages.html
│   │   ├── landing.html                 ← from index.html
│   │   ├── auth/
│   │   │   ├── register.html
│   │   │   └── login.html
│   │   ├── dashboard.html
│   │   ├── tournaments/
│   │   │   ├── list.html                ← from tournaments-list.html
│   │   │   ├── create.html              ← from tournaments-create.html
│   │   │   ├── detail.html              ← from tournament-detail.html
│   │   │   └── public.html              ← from tournament-public.html
│   │   ├── matches/
│   │   │   ├── scorecard.html
│   │   │   └── record.html
│   │   ├── users/
│   │   │   ├── profile.html
│   │   │   ├── profile_edit.html
│   │   │   └── player_stats.html
│   │   └── errors/
│   │       ├── 403.html
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   └── static/                  # copied verbatim from frontend-original/
│       ├── css/styles.css
│       └── js/
│           ├── main.js          # unchanged
│           ├── maps.js          # unchanged
│           ├── comments.js      # patched per §6.4 below
│           ├── livefeed.js      # unchanged
│           └── mockdata.js      # kept for now; removed page-by-page
│
├── migrations/                  # `flask db init` output
│
└── tests/
    ├── conftest.py              # app/db fixtures, client, auth helpers
    ├── unit/
    │   ├── test_auth.py
    │   ├── test_models.py
    │   ├── test_tournament_services.py
    │   ├── test_match_services.py
    │   ├── test_comments_api.py
    │   └── test_live_proxy.py
    └── selenium/
        ├── conftest.py          # live_server fixture, ChromeDriver
        ├── test_signup_login.py
        ├── test_create_tournament.py
        ├── test_record_match.py
        ├── test_public_share.py
        └── test_search_filter.py
```

> Why one model per file? The schema is 9 tables — a single `models.py` becomes hard to scan and hides circular-import risk between `Match`/`Innings`/`BattingEntry`. One file each, all re-exported via `models/__init__.py`, keeps imports flat.

---

## 4. Configuration

### 4.1 Environment variables (`.env.example`)

```env
# Flask
FLASK_APP=run:app
FLASK_ENV=development
SECRET_KEY=change-me-to-a-long-random-string

# Database
DATABASE_URL=sqlite:///instance/criktrack.sqlite3

# Auth
ORGANIZER_INVITE_CODE=criktrack-organizer-2026

# External APIs
GOOGLE_MAPS_API_KEY=
GOOGLE_MAPS_GEOCODING_API_KEY=
CRICKETDATA_API_KEY=

# Live feed cache
LIVE_FEED_CACHE_SECONDS=30
LIVE_FEED_POLL_MS=30000
```

- `.env` is **gitignored**. `.env.example` is committed and used by teammates.
- `SECRET_KEY` is mandatory. App refuses to start if it equals the placeholder string.
- `GOOGLE_MAPS_API_KEY` is the **browser-safe, HTTP-referrer-restricted** key, rendered into `window.CTM_CONFIG`. `GOOGLE_MAPS_GEOCODING_API_KEY` is server-side only (different IP-restricted key) — never sent to the client.
- `CRICKETDATA_API_KEY` is server-side only. Empty value disables the proxy, which then returns the upstream-failure shape so [livefeed.js](frontend-original/js/livefeed.js) falls back to `CTM_MOCK.liveFeed`.

### 4.2 Config classes (`config.py`)

```python
class BaseConfig:
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///instance/criktrack.sqlite3')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_TIME_LIMIT = 3600
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    CRICKETDATA_API_KEY = os.environ.get('CRICKETDATA_API_KEY', '')
    LIVE_FEED_CACHE_SECONDS = int(os.environ.get('LIVE_FEED_CACHE_SECONDS', 30))
    ORGANIZER_INVITE_CODE = os.environ.get('ORGANIZER_INVITE_CODE', '')

class DevConfig(BaseConfig):
    DEBUG = True

class TestConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False           # disabled for unit tests; Selenium tests re-enable
    SECRET_KEY = 'test-secret'

class ProdConfig(BaseConfig):
    SESSION_COOKIE_SECURE = True       # require HTTPS for the cookie
```

`create_app(config_class=DevConfig)` chooses the active class. `FLASK_ENV=production` triggers `ProdConfig`.

---

## 5. Application Factory & Extensions

### 5.1 `criktrack/extensions.py`

Singletons created here, bound in the factory:

```python
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
csrf = CSRFProtect()
```

### 5.2 `criktrack/__init__.py`

```python
def create_app(config_class=DevConfig) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Bind extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register blueprints
    from .auth import bp as auth_bp;            app.register_blueprint(auth_bp)
    from .users import bp as users_bp;          app.register_blueprint(users_bp)
    from .tournaments import bp as tour_bp;     app.register_blueprint(tour_bp, url_prefix='/tournaments')
    from .matches import bp as match_bp;        app.register_blueprint(match_bp)  # nested under tournaments
    from .players import bp as player_bp;       app.register_blueprint(player_bp)
    from .comments import bp as comments_bp;    app.register_blueprint(comments_bp, url_prefix='/api')
    from .live import bp as live_bp;            app.register_blueprint(live_bp,    url_prefix='/api/live')
    from .errors import bp as errors_bp;        app.register_blueprint(errors_bp)

    # Public landing route
    @app.route('/')
    def landing(): return render_template('landing.html')

    # Jinja filters + global context
    register_filters(app)
    register_context_processors(app)

    # CLI commands
    from .seed import seed_cli;                 app.cli.add_command(seed_cli)

    return app
```

### 5.3 `register_context_processors`

Inject the values [base.html](app/criktrack/templates/base.html) needs into every template (per §16.3 of the frontend plan):

```python
@app.context_processor
def inject_globals():
    return {
        'ctm_config': {
            'googleMapsApiKey': app.config['GOOGLE_MAPS_API_KEY'],
            'liveFeedEndpoint': url_for('live.matches'),
            'liveFeedPollMs': app.config.get('LIVE_FEED_POLL_MS', 30000),
        },
    }
```

`base.html` then writes:

```jinja
<meta name="csrf-token" content="{{ csrf_token() }}">
<script>window.CTM_CONFIG = {{ ctm_config|tojson }};</script>
<body data-ctm-role="{{ current_user.role.value if current_user.is_authenticated else 'user' }}">
```

This single attribute drives all role-gated CSS rules already present in [styles.css](frontend-original/css/styles.css).

---

## 6. Data Models

All models extend `db.Model`. Timestamps use `server_default=func.now()`.

### 6.1 User (`models/user.py`)

| Column         | Type                  | Notes                                                  |
| -------------- | --------------------- | ------------------------------------------------------ |
| `id`           | Integer PK            |                                                        |
| `email`        | String(254) UNIQUE    | indexed                                                |
| `display_name` | String(80) NOT NULL   |                                                        |
| `password_hash`| String(255) NOT NULL  | `werkzeug.security.generate_password_hash`             |
| `role`         | Enum('organizer','user') NOT NULL DEFAULT 'user' | `Role` Python enum                |
| `bio`          | Text NULLABLE         |                                                        |
| `avatar_url`   | String(255) NULLABLE  | future: file upload; for now just a URL or initials    |
| `location`     | String(120) NULLABLE  |                                                        |
| `created_at`   | DateTime NOT NULL     |                                                        |

Methods: `set_password(p)`, `check_password(p)`, `initials` (property), `to_dict()`.
Implements Flask-Login's `UserMixin` interface. `@login_manager.user_loader` defined alongside.

### 6.2 Tournament (`models/tournament.py`)

| Column         | Type                  | Notes                                                              |
| -------------- | --------------------- | ------------------------------------------------------------------ |
| `id`           | Integer PK            |                                                                    |
| `name`         | String(120) NOT NULL  |                                                                    |
| `description`  | Text NULLABLE         |                                                                    |
| `format`       | Enum NOT NULL         | `'round_robin' | 'knockout' | 'group_stage'`                       |
| `status`       | Enum NOT NULL         | `'upcoming' | 'live' | 'completed'`; recomputed by services       |
| `start_date`   | Date NOT NULL         |                                                                    |
| `team_count`   | Integer NOT NULL      | logical max; informs fixture generator                             |
| `organiser_id` | FK -> users.id        | NOT NULL; only organiser can edit                                  |
| `venue_id`     | FK -> venues.id       | NULLABLE; default location                                         |
| `share_slug`   | String(32) UNIQUE     | random; powers `/tournaments/<slug>/share`                         |
| `created_at`   | DateTime              |                                                                    |

Relationships: `teams`, `matches`, `comments`, `organiser`.

### 6.3 Team (`models/tournament.py`)

`id`, `tournament_id` (FK), `name`, `short_code` (3 char), `played`, `won`, `lost`, `points`, `nrr` (Numeric(4,2)). The standings columns are denormalised for read efficiency and recomputed in `tournaments.services.recompute_standings()`.

### 6.4 Player (`models/player.py`)

`id`, `team_id` (FK NULLABLE — free agents possible), `name`, `role` (`'batter' | 'bowler' | 'all_rounder' | 'wicket_keeper'`).

### 6.5 Venue (`models/venue.py`)

`id`, `name`, `address`, `lat` (Float), `lng` (Float). Geocoded once on create; `lat`/`lng` may be NULL if Google's key is absent or geocoding fails.

### 6.6 Match (`models/match.py`)

| Column          | Type            | Notes                                                  |
| --------------- | --------------- | ------------------------------------------------------ |
| `id`            | Integer PK      |                                                        |
| `tournament_id` | FK              |                                                        |
| `venue_id`      | FK NULLABLE     | falls back to `tournament.venue_id`                    |
| `team_a_id`     | FK -> teams.id  |                                                        |
| `team_b_id`     | FK -> teams.id  |                                                        |
| `scheduled_at`  | DateTime        | combines date + time fields from frontend              |
| `status`        | Enum            | `'upcoming' | 'live' | 'completed'`                    |
| `toss_winner_id`| FK NULLABLE     |                                                        |
| `toss_decision` | Enum NULLABLE   | `'bat' | 'bowl'`                                       |
| `winner_id`     | FK NULLABLE     |                                                        |
| `result_text`   | String(120)     | "Crusaders won by 17 runs"                             |
| `external_id`   | String(64) NULLABLE | optional CricketData.org pairing for live widget   |

### 6.7 Innings, BattingEntry, BowlingEntry (`models/match.py`)

- **Innings**: `id`, `match_id`, `batting_team_id`, `bowling_team_id`, `runs`, `wickets`, `overs` (Numeric(3,1)), `inning_number` (1 or 2 for T20).
- **BattingEntry**: `id`, `innings_id`, `player_id`, `runs`, `balls`, `fours`, `sixes`, `dismissal` (free text "c Rao b Khan"), `is_not_out` (bool).
- **BowlingEntry**: `id`, `innings_id`, `player_id`, `overs` (Numeric(3,1)), `maidens`, `runs`, `wickets`.

`strike_rate`/`economy` are computed properties, not stored.

### 6.8 Comment (`models/comment.py`)

| Column          | Type            | Notes                                                |
| --------------- | --------------- | ---------------------------------------------------- |
| `id`            | Integer PK      |                                                      |
| `match_id`      | FK NULLABLE     | NOT NULL when scoping to a match                     |
| `tournament_id` | FK NULLABLE     | NOT NULL when scoping to tournament-level comments   |
| `user_id`       | FK -> users.id  |                                                      |
| `body`          | String(500) NOT NULL | server validates <= 500 chars                   |
| `created_at`    | DateTime NOT NULL    |                                                  |

Constraint: exactly one of `match_id` / `tournament_id` is non-null.

`to_dict()` returns the JSON shape from §16.5 of the frontend plan, with `authorName`, `initials`, `role` denormalised from `comment.user`.

### 6.9 Indexing

| Index                                         | Why                                                             |
| --------------------------------------------- | --------------------------------------------------------------- |
| `users.email` UNIQUE                          | login lookup                                                    |
| `tournaments.share_slug` UNIQUE               | public share URL                                                |
| `tournaments.organiser_id`                    | dashboard filter                                                |
| `matches.tournament_id, scheduled_at`         | fixtures view sorts                                             |
| `comments.match_id, created_at DESC`          | newest-first feed                                               |

### 6.10 Migrations strategy

- One migration per logical milestone, not per model (avoids 9 trivial migrations on day one).
- Milestones: `0001_users.py`, `0002_tournaments_teams_players.py`, `0003_matches_innings.py`, `0004_comments.py`, plus any later additions as separate migrations.
- `flask db upgrade` is part of the README run-instructions and the test fixtures.

---

## 7. Authentication & Roles

### 7.1 Sign-up flow

1. `GET /register` renders [auth/register.html](app/criktrack/templates/auth/register.html) (Jinja port of [register.html](frontend-original/register.html)).
2. `POST /register` validates `RegisterForm`:
   - `email` unique, valid format
   - `password` ≥ 8 chars, mixed case + digit (validated client-side too in [main.js](frontend-original/js/main.js))
   - `password_confirm` matches
   - `terms` accepted
   - `invite_code` (optional) — if it equals `app.config['ORGANIZER_INVITE_CODE']`, the new user is `organizer`; otherwise `user` (default).
3. On success: `login_user(new_user)`, redirect to `dashboard`.

### 7.2 Login / logout

- `LoginForm`: email + password + remember-me checkbox.
- Always answer with the same generic error ("Invalid email or password") to avoid user enumeration.
- `POST /logout` is CSRF-protected and only accepts POST (avoids CSRF logout via image tag).

### 7.3 Password storage

- `werkzeug.security.generate_password_hash(pw, method='pbkdf2:sha256:600000', salt_length=16)` — explicit method for transparency in the README.
- Never log raw passwords; the `app.logger` redacts form bodies on error.

### 7.4 Role gating

- `Role` is a Python `enum.Enum` with values `organizer`, `user`. Stored as native SQL enum.
- Decorator `@require_role('organizer')` returns 403 + flash for HTML routes, 403 JSON for `Accept: application/json`.
- Applied to: `tournaments.create`, `tournaments.edit`, `matches.record` (GET + POST), team/player edit endpoints, comment delete (when not own).
- Frontend already gates buttons via `<body data-ctm-role>` (§16.2 of frontend plan); the decorator is the *real* enforcement.

### 7.5 Session security

- `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`, `SESSION_COOKIE_SECURE = True` in production.
- `WTF_CSRF_ENABLED = True` everywhere except unit tests.
- CSRF token surfaced to JS via `<meta name="csrf-token">` in `base.html`. AJAX requests in [comments.js](frontend-original/js/comments.js) (after the §16.5 patch) read it and send `X-CSRFToken`.

---

## 8. Routes & Blueprints

URL map (matching [checkpoint-2-doc.md](checkpoint-2-doc.md) §3 exactly):

| Method | URL                                                              | Endpoint                  | Auth         |
| ------ | ---------------------------------------------------------------- | ------------------------- | ------------ |
| GET    | `/`                                                              | `landing`                 | public       |
| GET    | `/register`                                                      | `auth.register`           | anon-only    |
| POST   | `/register`                                                      | `auth.register_post`      | anon-only    |
| GET    | `/login`                                                         | `auth.login`              | anon-only    |
| POST   | `/login`                                                         | `auth.login_post`         | anon-only    |
| POST   | `/logout`                                                        | `auth.logout`             | required     |
| GET    | `/dashboard`                                                     | `users.dashboard`         | required     |
| GET    | `/users/<int:id>`                                                | `users.profile`           | public       |
| GET    | `/profile/edit`                                                  | `users.profile_edit`      | required     |
| POST   | `/profile/edit`                                                  | `users.profile_edit_post` | required     |
| GET    | `/tournaments`                                                   | `tournaments.list`        | public       |
| GET    | `/tournaments/create`                                            | `tournaments.create`      | organizer    |
| POST   | `/tournaments/create`                                            | `tournaments.create_post` | organizer    |
| GET    | `/tournaments/<int:id>`                                          | `tournaments.detail`      | required     |
| GET    | `/tournaments/<slug>/share`                                      | `tournaments.public`      | public       |
| GET    | `/tournaments/<int:id>/matches/<int:match_id>`                   | `matches.scorecard`       | required     |
| GET    | `/tournaments/<int:id>/matches/<int:match_id>/record`            | `matches.record`          | organizer    |
| POST   | `/tournaments/<int:id>/matches/<int:match_id>/record`            | `matches.record_post`     | organizer    |
| GET    | `/tournaments/<int:id>/players/<int:player_id>`                  | `players.stats`           | required     |
| GET    | `/api/matches/<int:match_id>/comments`                           | `comments.list_match`     | public       |
| POST   | `/api/matches/<int:match_id>/comments`                           | `comments.create_match`   | required     |
| GET    | `/api/tournaments/<int:tournament_id>/comments`                  | `comments.list_tournament`| public       |
| POST   | `/api/tournaments/<int:tournament_id>/comments`                  | `comments.create_tour`    | required     |
| GET    | `/api/live/matches`                                              | `live.matches`            | public       |

The blueprint `url_prefix` settings in §5.2 yield these paths without per-route prefixing.

---

## 9. Forms (Flask-WTF)

Each `forms.py` defines one or two WTForms classes. Validation rules mirror the client-side rules already implemented in [main.js](frontend-original/js/main.js) so server and client errors line up.

| Form                | Fields                                                                                        |
| ------------------- | --------------------------------------------------------------------------------------------- |
| `RegisterForm`      | display_name, email, password, password_confirm, invite_code (opt), terms (BooleanField)      |
| `LoginForm`         | email, password, remember                                                                     |
| `ProfileEditForm`   | display_name, bio (TextArea ≤ 280), location, avatar_url                                      |
| `TournamentForm`    | name, description, format (SelectField), start_date, team_count, venue (subform: name/address)|
| `TeamForm`          | name, short_code, players (FieldList of StringField, ≥ team_count)                            |
| `MatchResultForm`   | toss_winner, toss_decision, winner, result_text — and JSON innings payload validated manually |

For `MatchResultForm`, the entry/edit page submits the full innings payload as JSON (the dynamic batter/bowler rows in [match-record.html](frontend-original/match-record.html) make a flat WTForms field list awkward). The view wraps the JSON in a Marshmallow-style hand-written validator (`matches.services.validate_payload`) and returns field-keyed error JSON for [main.js](frontend-original/js/main.js) to surface inline.

---

## 10. AJAX Endpoints

Three clusters of true AJAX (rest of the app is server-rendered Jinja with the existing JS for interactivity):

### 10.1 Comments — JSON list & create

Already specified in §16.5 of the frontend plan. Backend implementation:

- `GET /api/{matches|tournaments}/<id>/comments` → `[Comment.to_dict(), ...]`, `ORDER BY created_at DESC`. No auth required (read-only on public data).
- `POST /api/{matches|tournaments}/<id>/comments` (auth required, CSRF-protected):
  - 400 if body empty / > 500 chars.
  - On success: returns the created comment dict (so the client can prepend without re-fetching).
- Client patch for [comments.js](frontend-original/js/comments.js): replace the `CTM_MOCK.comments` reads with `fetch(url)` + `Promise.then(render)`; replace the in-memory `unshift` with `fetch(url, { method: 'POST', body: JSON.stringify(...), headers: { 'Content-Type': 'application/json', 'X-CSRFToken': metaToken } })`. Same CSS hooks; no markup change.

### 10.2 Match record — JSON submit

- `POST /tournaments/<tid>/matches/<mid>/record` accepts `application/json` payload:

```json
{
  "toss": { "winner_team_id": 11, "decision": "bat" },
  "result": { "winner_team_id": 11, "result_text": "won by 17 runs" },
  "innings": [
    {
      "batting_team_id": 11,
      "batting": [
        { "player_id": 51, "runs": 78, "balls": 52, "fours": 8, "sixes": 3,
          "dismissal": "c Rao b Khan", "is_not_out": false },
        ...
      ],
      "bowling": [
        { "player_id": 71, "overs": 4.0, "maidens": 0, "runs": 28, "wickets": 3 },
        ...
      ]
    },
    ...
  ]
}
```

Server response: `200` with `{ "redirect": "/tournaments/.../matches/501" }` on success, `400` with `{ errors: { "innings.0.batting.2.runs": "must be >= 0" } }` on validation failure. The frontend's existing `data-ctm-validate` flow already knows how to consume keyed errors.

### 10.3 Live cricket proxy

Per §16.6 of the frontend plan:

- `GET /api/live/matches` proxies CricketData.org `currentMatches`.
- 30-second TTL cache via `live.client.CachedClient` (a tiny in-process wrapper around `requests`).
- Fail-soft: upstream 5xx/429/timeout → return last successful payload with `X-CTM-Stale: 1`. Empty cache → return CTM_MOCK-shaped fallback object so [livefeed.js](frontend-original/js/livefeed.js) keeps rendering.
- API key never leaves the server.

---

## 11. Domain Services

Pure-Python helpers (no Flask context) that the routes delegate to. Easy to unit-test.

### 11.1 `tournaments/services.py`

- `generate_fixtures(tournament)` — round-robin (every team plays every other once), knockout (single-elimination bracket; pads with byes if `team_count` is not a power of 2), group-stage (split into groups of 4, round-robin within groups, top 2 advance).
- `recompute_standings(tournament)` — iterates completed matches, updates `Team.played/won/lost/points/nrr`. Called after every match save.
- `compute_nrr(team)` — `(runs scored / overs faced) - (runs conceded / overs bowled)` aggregated across the tournament.

### 11.2 `matches/services.py`

- `apply_match_result(match, payload, organiser)` — wraps validation + `db.session.add` + `recompute_standings`. Idempotent: editing an existing match removes the prior `Innings` rows first.
- `validate_payload(payload, match)` — returns `(cleaned_dict, errors_dict)`; rejects unknown player ids, negative numbers, runs > balls × 6, etc.

### 11.3 `players/services.py`

- `aggregate_for_player(player, tournament)` — sums `BattingEntry`/`BowlingEntry` across the tournament's matches and returns the dict shape `CTM_MOCK.player` exposes (`runs`, `average`, `strikeRate`, `fifties`, `hundreds`, `wickets`, `bowlingAvg`, `economy`, `matches[]`).

### 11.4 `live/client.py`

```python
class CachedCricketDataClient:
    BASE = 'https://api.cricapi.com/v1'

    def __init__(self, api_key, ttl=30): ...
    def current_matches(self) -> dict:        # cached by URL
        ...
```

Cache is a `dict[str, tuple[float, dict]]` guarded by `threading.Lock`. A class attribute, not instance, so tests can clear it between cases.

---

## 12. External Integrations

### 12.1 Google Maps

- **Geocoding (server-side, on tournament create):** `integrations/geocoding.py::geocode(address)` → `(lat, lng) | None`. Non-fatal: failure persists the venue without coordinates and the template hides the map block (`{% if venue.lat and venue.lng %}`).
- **Map rendering (browser):** unchanged — [maps.js](frontend-original/js/maps.js) consumes `data-lat`/`data-lng` from the venue block already specified in §16.4 of the frontend plan.

### 12.2 CricketData.org

Covered in §10.3 + §11.4 above. Free tier (100 k req/h) is well above what 30 s polling needs.

### 12.3 Key safety

- `GOOGLE_MAPS_API_KEY` shipped to client → must be HTTP-referrer restricted in Google Cloud Console.
- `GOOGLE_MAPS_GEOCODING_API_KEY` — server-only, IP-restricted.
- `CRICKETDATA_API_KEY` — server-only.
- `.env` is gitignored; `.env.example` is committed without values.

---

## 13. Error Handling

| Status | When                                              | Response                                                       |
| ------ | ------------------------------------------------- | -------------------------------------------------------------- |
| 400    | Form validation failure                           | HTML: re-render with errors. JSON: `{"errors": {...}}`         |
| 401    | Anonymous accessing protected route               | HTML: redirect to `/login?next=...`. JSON: `{"error":"auth"}`  |
| 403    | Wrong role / not the organiser                    | HTML: render `errors/403.html`. JSON: `{"error":"forbidden"}`  |
| 404    | Unknown id / slug                                 | HTML: render `errors/404.html`. JSON: `{"error":"not_found"}`  |
| 500    | Unhandled exception                               | HTML: render `errors/500.html`. Logged with stack trace.       |

`errors/handlers.py` registers an `app.errorhandler(...)` per status. Content negotiation is `request.accept_mimetypes.best_match(['application/json','text/html']) == 'application/json'`.

---

## 14. Logging

- Default logger writes to stderr.
- In production, `RotatingFileHandler` writes JSON-formatted records to `instance/logs/app.log`.
- Auth failures, role denials, and live-feed cache misses are info/warning logs (useful for debugging the integration during marking).
- Never log request bodies for `/login`, `/register`, `/profile/edit` — guarded by an explicit redactor.

---

## 15. Frontend Asset Migration

This is mostly file moves + a handful of small JS patches.

| What                                       | Action                                                                       |
| ------------------------------------------ | ---------------------------------------------------------------------------- |
| `frontend-original/css/styles.css`         | Copy to `app/criktrack/static/css/styles.css` unchanged                      |
| `frontend-original/js/{main,maps,livefeed,mockdata}.js` | Copy unchanged                                                  |
| `frontend-original/js/comments.js`         | Copy + patch: replace `CTM_MOCK.comments` reads with `fetch()`, in-memory append with `POST` |
| `frontend-original/js/config.js`           | **Delete.** Replaced by inline `<script>` in `base.html` (§5.3).             |
| `frontend-original/js/layout.js`           | **Delete.** `NAV_HTML`/`FOOTER_HTML` extracted to `partials/{nav,footer}.html` |
| `frontend-original/js/roles.js`            | Trim to dev-only switcher; keep behind `{% if config.DEBUG %}` in `base.html`. Real role comes from `<body data-ctm-role>` Jinja-rendered. |
| Each `frontend-original/*.html`            | Convert to a Jinja template extending `base.html`. Move `<main>` content into `{% block content %}`. Replace hard-coded mock values with `{{ }}` from the view context. |

Asset URL path stays `/static/...` (Flask default), matching the existing `<link>`/`<script>` tags' relative paths once they become `{{ url_for('static', filename='...') }}`.

---

## 16. Testing

### 16.1 pytest unit tests (≥ 5)

Targets the rubric's "5+ unit tests" bar. Each runs in-memory (`TestConfig`):

| File                           | What it covers                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------------ |
| `test_auth.py`                 | Register validates email + password + invite code; login uses hashed pw; logout      |
| `test_models.py`               | Password hash never equals raw; role enum default; comment XOR constraint            |
| `test_tournament_services.py`  | Round-robin generates `n*(n-1)/2` fixtures; standings recompute updates points/NRR   |
| `test_match_services.py`       | Innings payload validation rejects negative runs and unknown players; idempotent edit|
| `test_comments_api.py`         | GET returns DESC order; POST 401 when anon, 400 on > 500 chars, 200 on valid         |
| `test_live_proxy.py`           | Cache returns within TTL; upstream 500 yields `X-CTM-Stale: 1` header                |

### 16.2 Selenium tests (≥ 5)

Run against a live `pytest-flask` server using ChromeDriver (managed by `webdriver-manager`):

| File                          | Scenario                                                                              |
| ----------------------------- | ------------------------------------------------------------------------------------- |
| `test_signup_login.py`        | Register → auto-login → see dashboard greeting                                        |
| `test_create_tournament.py`   | Organiser creates a tournament, dynamic team rows, redirect to detail, fixtures shown |
| `test_record_match.py`        | Organiser opens record page, fills batting + bowling rows, saves, sees scorecard      |
| `test_public_share.py`        | Anonymous visits `/tournaments/<slug>/share`, sees standings + live widget, no nav CTA|
| `test_search_filter.py`       | Search "UWA" + click "live" pill — only matching cards remain visible                 |

### 16.3 Test infrastructure

- `tests/conftest.py` provides `app`, `client`, `db_session`, `auth_as(role)` fixtures.
- `tests/selenium/conftest.py` boots a live server on a free port (pytest-flask), spins ChromeDriver in headless mode by default.
- CI-friendly: a single `pytest` command runs both suites; selenium tests can be skipped via `pytest -m "not selenium"`.

---

## 17. Security Checklist (rubric "Security" line)

- [x] Passwords stored as PBKDF2-SHA256 hashes with per-user salt
- [x] CSRF tokens on every form (Flask-WTF) and on all state-changing AJAX (X-CSRFToken)
- [x] `SESSION_COOKIE_HTTPONLY = True`; `SESSION_COOKIE_SAMESITE = 'Lax'`; `Secure` in prod
- [x] `SECRET_KEY` and all third-party API keys read from `.env`, never committed
- [x] Server-side role enforcement in addition to UI gating
- [x] Email enumeration guard on login
- [x] Output escaping by default (Jinja autoescape)
- [x] No raw SQL; all queries via SQLAlchemy ORM
- [x] Comment body capped at 500 chars on both client and server
- [x] Logout requires POST to defeat CSRF logout

---

## 18. Implementation Order (the actual sequence to code in)

Each milestone is independently testable so the team can review incrementally.

1. **Scaffold + factory**
   - `requirements.txt`, `.env.example`, `.gitignore`, `config.py`, `extensions.py`, `criktrack/__init__.py`, `run.py`, error handlers, base templates with the nav/footer extracted from [layout.js](frontend-original/js/layout.js). End state: `flask run` serves a styled landing page.
2. **Models + first migration**
   - User → migration `0001`. Other models → `0002`–`0004`. End state: `flask db upgrade` creates the schema.
3. **Auth + dashboard**
   - Register/login/logout, `users.dashboard`, `users.profile`, `profile/edit`. Role gating decorator. End state: a teammate can sign up and reach the dashboard.
4. **Tournaments CRUD + listing + detail**
   - Create form with team rows, fixture generation service, list/search page, public share page. End state: an organiser can create a tournament and see it in the list and detail views.
5. **Matches scorecard + record**
   - Scorecard read view, record JSON endpoint, dynamic batter/bowler rows wired through to validation, standings recomputation. End state: organiser records a match, scorecard shows the innings, standings update.
6. **Player stats**
   - Per-player aggregate page using `players.services.aggregate_for_player`. End state: clicking a top performer shows their per-tournament stats.
7. **Comments API + frontend patch**
   - REST endpoints, `comments.js` patched to call them. End state: any logged-in user can comment; organiser comments render with the badge.
8. **Live cricket proxy**
   - `live/client.py` + `live/routes.py`, `.env` wiring, public tournament page polls it. End state: with a real key, live widget shows upstream data; without a key it gracefully shows the sample with the "sample" badge.
9. **Google Maps geocoding**
   - On tournament create, geocode venue address; store lat/lng; map renders on detail + scorecard.
10. **Tests**
    - Unit suite first (fast feedback), then Selenium. Wire a `pytest` invocation in the README.
11. **Security pass + README**
    - Re-check §17, document setup/run/test commands in `app/README.md` and update root `README.md` per rubric.

Estimated effort if all three contributors work in parallel along the existing frontend split: ~2 weeks of part-time work.

---

## 19. Open Questions / Risks

- **Avatar uploads.** [profile-edit.html](frontend-original/profile-edit.html) shows an avatar field. Plan stores `avatar_url` (string) only; actual file upload (Flask-Reuploaded or similar) is out of scope unless a teammate volunteers. Initials fallback is already shipped.
- **Score-by-score live update.** The frontend polls `/api/live/matches` every 30 s but does **not** subscribe to local matches. If we want our own matches to auto-refresh, the current poll endpoint can be reused (`live.matches` could detect a `?source=local` param and return our DB rows shaped like CricketData) — flagged for a stretch goal, not the baseline.
- **Knockout fixture seeding.** Round-robin is trivial; knockout pairing depends on a manual seed list. Plan: default to alphabetical seeding, allow drag-reorder later.
- **Public-share read-only enforcement.** The public page must hide comment forms and any organiser actions. Implementation: pass `is_public=True` into the template context; the existing `data-role-gate` CSS handles the rest as long as `<body data-ctm-role="user">` is forced for that route.
- **Selenium in CI.** Headless Chrome works locally; if the team adds GitHub Actions, the workflow needs to install Chrome and matching ChromeDriver — a documented Action exists but is out of scope for this plan.
