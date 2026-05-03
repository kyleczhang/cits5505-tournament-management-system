# Database Design — CRIKTRACK

Companion to `README.md` and `plan-backend.md`. This document captures the schema and the backend services that read/write it.

- **Engine:** SQLite 3 via Flask-SQLAlchemy (`sqlite:///criktrack.sqlite3` in `app/instance/`).
- **ORM:** SQLAlchemy 2.0.31 (declarative style, `db.Column` / `db.relationship`).
- **Migrations:** Flask-Migrate (Alembic). Single revision `81e7747a2db2_initial_schema` covers the entire schema; a fresh `flask db upgrade` produces a schema that autogenerate-compares with **0 diffs** against the live models.
- **Models:** `app/criktrack/models/` — one module per aggregate (`user.py`, `tournament.py`, `match.py`, `player.py`, `venue.py`, `comment.py`).

---

## 1. Entity–relationship overview

```
User ──1───* Tournament (organiser)          Tournament ───1───? Venue
 │                   │                              │
 │                   ├─1─* Team ─1─* Player         │
 │                   │                              │
 │                   └─1─* Match ─1─* Innings ─1─* BattingEntry ─*─1 Player
 │                        │          └──────────1─* BowlingEntry ─*─1 Player
 │                        └─?─1 Venue
 │
 └─1─* Comment ─?─1 Match
             └──?─1 Tournament          (exactly one of match/tournament set)
```

- `User` can organise many `Tournaments`; regular users have `role=user`, organisers `role=organizer`.
- `Tournament` is the top-level aggregate; deleting one cascades to its `teams`, `matches` and `comments`.
- A `Match` has exactly two `Team` references (`team_a`, `team_b`, plus optional `toss_winner`/`winner`) and 0–2 `Innings` rows.
- `BattingEntry` / `BowlingEntry` rows are scoped to an `Innings`, each pointing at a `Player`.
- `Comment` is discriminated: `match_id XOR tournament_id` is non-null (enforced by a CHECK constraint).
- `Venue` is shared — a tournament and its matches may both reference the same venue row.

---

## 2. Tables

### 2.1 `users`

| Column          | Type                         | Constraints                                     | Notes                                         |
| --------------- | ---------------------------- | ----------------------------------------------- | --------------------------------------------- |
| `id`            | INTEGER                      | PK                                              |                                               |
| `email`         | VARCHAR(254)                 | NOT NULL, UNIQUE, INDEX                         | Lower-cased at insert                         |
| `display_name`  | VARCHAR(80)                  | NOT NULL                                        |                                               |
| `password_hash` | VARCHAR(255)                 | NOT NULL                                        | `pbkdf2:sha256:600000` via `werkzeug.security` |
| `role`          | ENUM(`organizer`, `user`)    | NOT NULL, default `user`                        | `Role` enum                                   |
| `bio`           | TEXT                         | NULL                                            |                                               |
| `avatar_url`    | VARCHAR(255)                 | NULL                                            |                                               |
| `location`      | VARCHAR(120)                 | NULL                                            |                                               |
| `created_at`    | DATETIME                     | NOT NULL, default `utcnow`                      |                                               |

Relationships: `organised_tournaments` (→ `tournaments.organiser_id`, lazy dynamic), `comments` (→ `comments.user_id`).

### 2.2 `tournaments`

| Column         | Type                                                | Constraints                       | Notes                                         |
| -------------- | --------------------------------------------------- | --------------------------------- | --------------------------------------------- |
| `id`           | INTEGER                                             | PK                                |                                               |
| `name`         | VARCHAR(120)                                        | NOT NULL                          |                                               |
| `description`  | TEXT                                                | NULL                              |                                               |
| `format`       | ENUM(`round_robin`, `knockout`, `group_stage`)      | NOT NULL, default `round_robin`   | `TournamentFormat`                            |
| `status`       | ENUM(`upcoming`, `live`, `completed`)               | NOT NULL, default `upcoming`, INDEX | `TournamentStatus`                          |
| `start_date`   | DATE                                                | NOT NULL                          |                                               |
| `team_count`   | INTEGER                                             | NOT NULL, default 0               | Denormalised; set at create time              |
| `organiser_id` | INTEGER                                             | NOT NULL, FK `users.id`, INDEX    |                                               |
| `venue_id`     | INTEGER                                             | NULL, FK `venues.id`              |                                               |
| `share_slug`   | VARCHAR(32)                                         | NOT NULL, UNIQUE, INDEX           | `secrets.token_urlsafe(9)` at row creation    |
| `created_at`   | DATETIME                                            | NOT NULL, default `utcnow`        |                                               |

Relationships: `organiser` (User), `venue` (lazy="joined"), `teams`, `matches`, `comments` — all with `cascade="all, delete-orphan"` on the collection side so a tournament deletion wipes its entire subtree.

### 2.3 `teams`

| Column          | Type         | Constraints                      | Notes                                    |
| --------------- | ------------ | -------------------------------- | ---------------------------------------- |
| `id`            | INTEGER      | PK                               |                                          |
| `tournament_id` | INTEGER      | NOT NULL, FK, INDEX              |                                          |
| `name`          | VARCHAR(80)  | NOT NULL                         |                                          |
| `short_code`    | VARCHAR(4)   | NOT NULL, default `???`          | Used for team logos in the UI            |
| `played`        | INTEGER      | NOT NULL, default 0              | **Denormalised** — recomputed by services |
| `won`           | INTEGER      | NOT NULL, default 0              | ditto                                    |
| `lost`          | INTEGER      | NOT NULL, default 0              | ditto                                    |
| `points`        | INTEGER      | NOT NULL, default 0              | `won × 2`                                |
| `nrr`           | NUMERIC(5,2) | NOT NULL, default 0              | Net run rate                             |

Why denormalise standings? The points table is the single most-read artefact per tournament; joining across `matches → innings → aggregates` on every render was measurable even at demo scale. The columns are authoritative but never hand-edited — see §4.3.

### 2.4 `players`

| Column    | Type                                                          | Constraints             | Notes                              |
| --------- | ------------------------------------------------------------- | ----------------------- | ---------------------------------- |
| `id`      | INTEGER                                                       | PK                      |                                    |
| `team_id` | INTEGER                                                       | NULL, FK `teams.id`     | Nullable to allow orphan imports   |
| `name`    | VARCHAR(80)                                                   | NOT NULL                |                                    |
| `role`    | ENUM(`batter`, `bowler`, `all_rounder`, `wicket_keeper`)      | NOT NULL, default `all_rounder` | `PlayerRole`               |

Players are auto-created by name at match-record time if no matching `(team_id, name)` exists — see `_player_for()` in `matches/services.py`. This avoids forcing organisers to pre-populate rosters.

### 2.5 `venues`

| Column    | Type         | Constraints | Notes                                 |
| --------- | ------------ | ----------- | ------------------------------------- |
| `id`      | INTEGER      | PK          |                                       |
| `name`    | VARCHAR(160) | NOT NULL    |                                       |
| `address` | VARCHAR(255) | NOT NULL    |                                       |
| `lat`     | FLOAT        | NULL        | Populated by Google Geocoding if available |
| `lng`     | FLOAT        | NULL        | ditto                                 |

Helper: `Venue.has_coords` → `lat is not None and lng is not None`.

### 2.6 `matches`

| Column            | Type                                          | Constraints                       | Notes                    |
| ----------------- | --------------------------------------------- | --------------------------------- | ------------------------ |
| `id`              | INTEGER                                       | PK                                |                          |
| `tournament_id`   | INTEGER                                       | NOT NULL, FK, INDEX               |                          |
| `venue_id`        | INTEGER                                       | NULL, FK `venues.id`              |                          |
| `team_a_id`       | INTEGER                                       | NOT NULL, FK `teams.id`           |                          |
| `team_b_id`       | INTEGER                                       | NOT NULL, FK `teams.id`           |                          |
| `scheduled_at`    | DATETIME                                      | NOT NULL, default `utcnow`        |                          |
| `status`          | ENUM(`upcoming`, `live`, `completed`)         | NOT NULL, default `upcoming`      | `MatchStatus`            |
| `toss_winner_id`  | INTEGER                                       | NULL, FK `teams.id`               |                          |
| `toss_decision`   | ENUM(`bat`, `bowl`)                           | NULL                              | `TossDecision`           |
| `winner_id`       | INTEGER                                       | NULL, FK `teams.id`               |                          |
| `result_text`     | VARCHAR(160)                                  | NULL                              | e.g. "Aces won by 20 runs" |
| `external_id`     | VARCHAR(64)                                   | NULL                              | Reserved for live-feed linking |

Composite index `ix_matches_tournament_scheduled` on `(tournament_id, scheduled_at)` to keep the fixtures page fast.

### 2.7 `innings`

| Column             | Type         | Constraints                 | Notes                 |
| ------------------ | ------------ | --------------------------- | --------------------- |
| `id`               | INTEGER      | PK                          |                       |
| `match_id`         | INTEGER      | NOT NULL, FK, INDEX         |                       |
| `inning_number`    | INTEGER      | NOT NULL, default 1         | 1 or 2                |
| `batting_team_id`  | INTEGER      | NOT NULL, FK `teams.id`     |                       |
| `bowling_team_id`  | INTEGER      | NOT NULL, FK `teams.id`     |                       |
| `runs`             | INTEGER      | NOT NULL, default 0         |                       |
| `wickets`          | INTEGER      | NOT NULL, default 0         | ≤ 10 (validated)      |
| `overs`            | NUMERIC(4,1) | NOT NULL, default 0         | e.g. `20.0`           |

Cascade-deletes its `batting_entries` + `bowling_entries`.

### 2.8 `batting_entries`

| Column         | Type         | Constraints           | Notes                          |
| -------------- | ------------ | --------------------- | ------------------------------ |
| `id`           | INTEGER      | PK                    |                                |
| `innings_id`   | INTEGER      | NOT NULL, FK, INDEX   |                                |
| `player_id`    | INTEGER      | NOT NULL, FK          |                                |
| `runs`         | INTEGER      | NOT NULL, default 0   |                                |
| `balls`        | INTEGER      | NOT NULL, default 0   |                                |
| `fours`        | INTEGER      | NOT NULL, default 0   |                                |
| `sixes`        | INTEGER      | NOT NULL, default 0   |                                |
| `dismissal`    | VARCHAR(160) | NULL                  | Free-text, e.g. "c Rao b Khan" |
| `is_not_out`   | BOOLEAN      | NOT NULL, default 0   |                                |

Derived property: `strike_rate = round(runs / balls * 100, 1)` (0.0 if `balls == 0`).

### 2.9 `bowling_entries`

| Column       | Type         | Constraints           | Notes              |
| ------------ | ------------ | --------------------- | ------------------ |
| `id`         | INTEGER      | PK                    |                    |
| `innings_id` | INTEGER      | NOT NULL, FK, INDEX   |                    |
| `player_id`  | INTEGER      | NOT NULL, FK          |                    |
| `overs`      | NUMERIC(4,1) | NOT NULL, default 0   |                    |
| `maidens`    | INTEGER      | NOT NULL, default 0   |                    |
| `runs`       | INTEGER      | NOT NULL, default 0   |                    |
| `wickets`    | INTEGER      | NOT NULL, default 0   |                    |

Derived property: `economy = round(runs / overs, 2)` (0.0 if `overs == 0`).

### 2.10 `comments`

| Column          | Type         | Constraints                                    | Notes                                     |
| --------------- | ------------ | ---------------------------------------------- | ----------------------------------------- |
| `id`            | INTEGER      | PK                                             |                                           |
| `match_id`      | INTEGER      | NULL, FK `matches.id`, INDEX                   | Exactly one of match/tournament is set    |
| `tournament_id` | INTEGER      | NULL, FK `tournaments.id`, INDEX               | ditto                                     |
| `user_id`       | INTEGER      | NOT NULL, FK `users.id`                        |                                           |
| `body`          | VARCHAR(500) | NOT NULL                                       | Enforced server + client side             |
| `created_at`    | DATETIME     | NOT NULL, default `utcnow`                     |                                           |

Table-level `CHECK ((match_id IS NOT NULL) <> (tournament_id IS NOT NULL))` (`ck_comment_target_xor`) makes the XOR invariant a hard DB rule rather than a service convention.

---

## 3. Enum reference

| Enum                | Values                                              | Source                   |
| ------------------- | --------------------------------------------------- | ------------------------ |
| `Role`              | `organizer`, `user`                                 | `models/user.py`         |
| `TournamentFormat`  | `round_robin`, `knockout`, `group_stage`            | `models/tournament.py`   |
| `TournamentStatus`  | `upcoming`, `live`, `completed`                     | `models/tournament.py`   |
| `MatchStatus`       | `upcoming`, `live`, `completed`                     | `models/match.py`        |
| `TossDecision`      | `bat`, `bowl`                                       | `models/match.py`        |
| `PlayerRole`        | `batter`, `bowler`, `all_rounder`, `wicket_keeper`  | `models/player.py`       |

All enums are `str, enum.Enum` — stored as their `.value` string in the DB, so hand-written queries stay readable.

---

## 4. Backend on top of the schema

Below are the places where code writes to or derives views from the schema. The aim is that routes stay thin and the invariants live in services.

### 4.1 Auth (`auth/routes.py`)

- Registration hashes the password with `werkzeug.generate_password_hash("pbkdf2:sha256:600000", salt_length=16)` before insert. Role is `organizer` iff the submitted invite code equals `ORGANIZER_INVITE_CODE`, else `user`.
- Email is always lower-cased before persistence and lookup — prevents duplicate accounts by case.
- `_safe_next()` rejects external hosts and protocol-relative URLs before honouring `?next=`, closing an open-redirect vector.

### 4.2 Tournament create (`tournaments/routes.py::create`)

One transaction:

1. Optionally create a `Venue`, calling `geocode_address()` to populate `lat`/`lng` when a Google key is configured — failure is non-fatal.
2. Insert `Tournament` with `share_slug = secrets.token_urlsafe(9)` (set by the model default), `team_count = len(team_names)`.
3. Insert `Team` rows with auto-generated `short_code` (first three uppercase alpha chars of the team name, fallback `TBD`).

All inserts share a single `db.session.commit()`.

### 4.3 Match result (`matches/services.py`)

This is the most load-bearing service. Entry points:

- `validate_payload(payload, match) -> dict`
  - Checks toss winner / result winner are one of the two teams in *this* match.
  - `wickets ≤ 10`, non-negative numeric fields.
  - Batting and bowling rows with blank player names are silently dropped (UI adds+removes rows freely).
  - Aggregates field errors and raises `ValidationError(errors)` — the route turns that into `{"errors": {...}} HTTP 400`.

- `save_result(match, normalised) -> Match`
  - Wipes existing `Innings` (cascade clears `BattingEntry` + `BowlingEntry`).
  - Inserts new `Innings` rows, calling `_player_for(name, team_id)` to find-or-create players.
  - Sets `match.winner_id`, `match.result_text`, `match.toss_*`, and `match.status = COMPLETED` if a winner was provided, else `LIVE`.
  - Commits, then calls `_recompute_standings(match)`.

- `_recompute_standings(match)`
  - Zeros out `played/won/lost/points/nrr` for every team in the tournament.
  - Iterates all `MatchStatus.COMPLETED` matches with `joinedload(Match.innings)`.
  - Increments `played` for both sides and `won + points+=2` for the winner (`points = won × 2`, no bonus points yet).
  - Accumulates `runs_for`, `runs_against`, `overs_for`, `overs_against` per team to compute `nrr = (runs_for/overs_for) − (runs_against/overs_against)`, rounded to 2 decimal places.
  - Commits.

**Why recompute instead of incrementally updating?** Editing an already-recorded result would otherwise require diffing the old and new innings — error-prone. A full rebuild is O(matches_in_tournament × avg_innings), which stays cheap at the scale we target (a league with ~30 matches), and is provably consistent with the audit trail.

### 4.4 Player stats (`players/routes.py::stats`)

Join-heavy read that never writes. Given `(tournament_id, player_id)`:

1. Verify `player.team.tournament_id == tournament_id`, else 404 (cross-tournament isolation).
2. Pull `BattingEntry` rows joined through `Innings → Match` and filtered on the tournament + player.
3. Pull `BowlingEntry` rows the same way.
4. Build two summaries: aggregate stats (matches, runs, average, SR, fifties/hundreds, highest, wickets, economy, bowling average) and a per-match history list ordered by `match.scheduled_at` desc.

All derivations live in the route; nothing is persisted.

### 4.5 Comments (`comments/routes.py`)

Four endpoints, two per target:

- `GET /api/{matches|tournaments}/<id>/comments` — returns `[Comment.to_dict()]` ordered `created_at` desc.
- `POST /api/{matches|tournaments}/<id>/comments` — requires auth (`current_user.is_authenticated`, else `abort(401)`), strips whitespace, enforces `0 < len(body) ≤ 500`, inserts, returns `201` with the created comment.

The XOR check constraint on the table means even a buggy service can't accidentally create a "both set" or "neither set" comment.

### 4.6 Live-feed proxy (`integrations/cricketdata.py`)

Not stored in the DB. Kept here because `matches.external_id` is the intended integration point if we later want to merge live IDs with our `matches` rows.

### 4.7 Geocoding (`integrations/geocoding.py`)

Called synchronously inside the tournament-create transaction. Returns `(lat, lng) | None`. A `None` return is normal — the DB keeps `venues.lat`/`lng` nullable precisely so the UI can fall back to OpenStreetMap rendering when we have no coords.

---

## 5. Migrations workflow

Single revision today:

```
81e7747a2db2 – initial schema: users, tournaments, teams, players, venues,
               matches, innings, batting/bowling entries, comments
```

Operational notes:

- `flask --app run:app db upgrade` brings an empty database up to head.
- Any model change must be accompanied by an autogenerated revision: `flask --app run:app db migrate -m "add ..."` — **always review the diff** before committing, especially SQLite ops (Alembic sometimes proposes column moves as drop/recreate).
- A sanity check runs in CI-equivalent form: `compare_metadata(migration_applied_db, db.metadata)` should report zero diffs. Today the check is clean.

---

## 6. Data integrity summary

Guarantees the DB enforces (not just the services):

- **Unique email** per user.
- **Unique share_slug** per tournament.
- **NOT NULL** on every FK that represents ownership (tournament → organiser, match → tournament, innings → match, entries → innings + player).
- **Comment XOR target** — DB CHECK constraint.
- **Cascade deletes** along every ownership edge, so deleting a tournament leaves no orphans.
- **Enum validation** — invalid status/format/role values are rejected at insert time by SQLAlchemy's Enum type.

Guarantees handled in the service layer (not the DB) because they span multiple rows:

- Match winner must be one of the two match teams.
- At most one innings per team per match (implicitly — `save_result` writes fresh innings after wiping).
- Standings columns are consistent with completed matches — maintained by `_recompute_standings`.
- Comment body length ≤ 500 chars (backed by VARCHAR(500) so the DB still truncates as a last resort).

---

## 7. Seed data

`flask --app run:app seed` (see `criktrack/seed.py`) loads:

- 3 users (1 organiser, 2 regular), all with password `password123`.
- 1 venue (UWA Sports Park) with real lat/lng.
- 6 tournaments (1 primary with six teams + a completed match, 5 "dashboard filler" rows).
- 6 teams + 13 players for the primary tournament.
- 1 completed match with 13 batting entries, 10 bowling entries spanning two innings.
- 3 comments on that match (from the three seeded users).

Pass `--reset` to wipe and re-seed. Safe to run repeatedly — idempotent without `--reset` (exits early if users exist).
