# CRIKTRACK V2 Implementation Plan

## Purpose

This document defines a phased implementation plan for CRIKTRACK V2 based on the current codebase.
It is intended to be used as a working reference during the refactor and feature delivery process.

The target product direction is documented in [product-v2.md](/Users/chengzhang/Desktop/project/cits5505-tms/docs/product-v2.md).

## Current-State Constraints

The current codebase does not yet match the V2 product direction.
The most important gaps are:

- `Team` is currently modeled as a child of `Tournament`, not as a reusable global entity.
- tournament creation currently creates new teams from free-text input.
- there is no real team management or roster management flow.
- there is no match creation flow.
- match result entry currently accepts free-text player names and implicitly creates missing players.
- standings are currently stored directly on `Team`, which only works when a team belongs to exactly one tournament.

Because of these constraints, implementation must start with the data model and service-layer refactor before UI-only work.

## Guiding Principles

- Refactor the domain model first, then rebuild UI flows on top of it.
- Avoid partial compatibility layers unless they materially reduce risk.
- Keep V2 limited to one roster layer: `Team -> Player`.
- Do not introduce tournament-specific rosters in V2.
- Preserve current derived-data behavior: standings and player statistics must continue to be recalculated from match data.

## Target V2 Domain Model

The target V2 model should be:

- `Team`: reusable team entity
- `Player`: belongs to one team
- `Tournament`: competition
- `TournamentTeam`: a team's participation in a tournament, including standings fields
- `Match`: belongs to one tournament and references two teams

`Fixture` should remain a product concept only, not a separate model.

## Phase 0: Confirm the Target Model

### Goal

Lock the domain model before editing the code.

### Why this phase is necessary

The current implementation stores standings on `Team`.
That design is incompatible with the new product direction where teams are reusable across tournaments.

If `Team` becomes reusable, standings must move to a tournament-specific participation layer.

### Decisions to finalize

- `Team` becomes a global reusable entity
- `Player` remains attached directly to `Team`
- `TournamentTeam` is added as the tournament participation model
- standings fields move from `Team` to `TournamentTeam`
- `Match.team_a_id` and `Match.team_b_id` continue to point to `Team`

### Deliverables

- final agreed entity relationships
- final naming decision for `TournamentTeam`
- confirmation that V2 will not include tournament-specific rosters

## Phase 1: Refactor Models and Database Schema

### Goal

Change the persistence model so it matches the V2 product rules.

### Current code affected

- [app/criktrack/models/tournament.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/models/tournament.py)
- [app/criktrack/models/player.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/models/player.py)
- [app/criktrack/models/match.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/models/match.py)
- [app/criktrack/models/__init__.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/models/__init__.py)
- [app/migrations/versions/81e7747a2db2_initial_schema_users_tournaments_teams_.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/migrations/versions/81e7747a2db2_initial_schema_users_tournaments_teams_.py)

### Planned changes

- move `Team` to a reusable global model
- remove `Team.tournament_id`
- remove standings fields from `Team`
- add team ownership if required by organizer-scoped management
- add `TournamentTeam` with:
  - `tournament_id`
  - `team_id`
  - `played`
  - `won`
  - `lost`
  - `points`
  - `nrr`
- keep `Player.team_id`
- keep `Match.tournament_id`
- keep `Match.team_a_id` and `Match.team_b_id`, but enforce that both teams are registered in the tournament

### Notes

- This phase should be treated as a cut-over, not a soft migration with dual behavior.
- The migration will require coordinated changes to tests and seed data later.

### Exit criteria

- schema migration is complete
- models import cleanly
- the app boots with the new schema

## Phase 2: Build Team and Roster Management

### Goal

Introduce the missing management flow for global teams and their players.

### Current gap

There is no dedicated team management flow.
Player management is not modeled as a proper roster workflow.

### Planned features

- team list page
- create team page
- edit team page
- team detail page
- roster management section on team detail
- add player
- edit player
- remove player

### Business rules

- players are managed from the team roster page
- assigning a player to a team is not a separate primary workflow
- if free-agent players are no longer needed, `Player.team_id` should become non-nullable

### Current code affected

- [app/criktrack/models/player.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/models/player.py)
- [app/criktrack/players/routes.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/players/routes.py)
- new `teams` blueprint or equivalent route additions
- related templates and tests

### Exit criteria

- organizer can create teams independently
- organizer can manage players through a team roster page
- player creation no longer depends on score entry

## Phase 3: Rebuild Tournament Creation Around Existing Teams

### Goal

Make tournament creation use existing teams instead of free-text team input.

### Current code affected

- [app/criktrack/tournaments/forms.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/tournaments/forms.py)
- [app/criktrack/tournaments/routes.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/tournaments/routes.py)
- [app/criktrack/templates/tournaments/create.html](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/templates/tournaments/create.html)

### Current behavior to remove

- tournament creation dynamically accepts raw team names
- tournament creation directly inserts new `Team` records

### Planned changes

- tournament creation creates only the tournament itself
- participating teams are selected from existing database records
- selection should use a searchable multi-select UI
- submitting the form creates `TournamentTeam` records
- `team_count` should either become derived or be maintained consistently through service-layer logic

### Service-layer recommendation

Move tournament creation and team-assignment logic into a dedicated service instead of keeping all business rules inside the route.

### Exit criteria

- free-text team creation is removed from the tournament creation flow
- tournaments only accept existing teams
- tournament detail can show the registered teams from `TournamentTeam`

## Phase 4: Add Match Scheduling and Management

### Goal

Add the missing flow for creating and managing tournament matches.

### Current gap

The codebase can display matches and record results, but it cannot create matches through the product UI.

### Current code affected

- [app/criktrack/matches/routes.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/matches/routes.py)
- [app/criktrack/templates/tournaments/detail.html](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/templates/tournaments/detail.html)
- new forms, templates, services, and tests

### Planned features

- create match page
- tournament match management page
- manual match creation
- optional simple fixture generation later

### Business rules

- both teams in a match must already be registered in the tournament
- a team cannot play itself
- every match must include `scheduled_at`
- match starts as `UPCOMING`

### Exit criteria

- organizer can create matches under a tournament
- tournament fixtures are no longer read-only
- dashboard `Schedule` reminders have a real destination flow

## Phase 5: Make Score Entry Roster-Safe

### Goal

Stop score entry from creating new players and restrict entries to existing roster members.

### Current code affected

- [app/criktrack/matches/services.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/matches/services.py)
- [app/criktrack/matches/routes.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/matches/routes.py)
- [app/criktrack/templates/matches/record.html](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/templates/matches/record.html)
- [app/criktrack/static/js/record.js](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/static/js/record.js)

### Current behavior to remove

- free-text player-name entry as the main mechanism
- implicit player creation via `_player_for()`

### Planned changes

- replace free-text player entry with roster-based selectors
- frontend submits `player_id` rather than raw player name
- validate that each selected player belongs to one of the two teams in the match
- remove automatic player creation during score entry

### Exit criteria

- score entry only accepts valid existing players
- recording a result cannot create new players
- player statistics remain clean and deterministic

## Phase 6: Rewire Standings, Dashboard, and Dependent Queries

### Goal

Move all tournament-dependent team logic from `Team` to `TournamentTeam`.

### Current code affected

- [app/criktrack/matches/services.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/matches/services.py)
- [app/criktrack/tournaments/routes.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/tournaments/routes.py)
- [app/criktrack/users/routes.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/users/routes.py)
- public tournament views
- follow-related display queries

### Planned changes

- standings recomputation updates `TournamentTeam`, not `Team`
- tournament detail standings read from `TournamentTeam`
- dashboard summaries that currently iterate tournament-owned teams must be updated
- tournament team counts must come from tournament registrations
- any logic assuming `Team.tournament_id` must be rewritten

### Special care areas

- `Needs your attention`
- dashboard player counts
- team follow widgets
- player stats routing assumptions

### Exit criteria

- standings are fully tournament-scoped
- dashboard and public views behave correctly with reusable teams
- no query still assumes `Team.tournament_id`

## Phase 7: Update Seed Data, Tests, and Documentation

### Goal

Bring all development tooling and verification layers in line with the refactor.

### Current code affected

- [app/criktrack/seed.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/criktrack/seed.py)
- [app/tests/unit/test_dashboard.py](/Users/chengzhang/Desktop/project/cits5505-tms/app/tests/unit/test_dashboard.py)
- other unit tests that directly construct `Team(tournament_id=...)`
- README and design docs where necessary

### Planned changes

- update seed flow to create global teams first
- register teams into tournaments through `TournamentTeam`
- update all test fixtures and helper factories
- remove or rewrite tests that depend on teamless players if that concept is removed
- add tests for:
  - team CRUD
  - roster CRUD
  - tournament creation from existing teams
  - match creation
  - result entry rejecting unknown players
  - standings recomputation through `TournamentTeam`

### Exit criteria

- `.venv/bin/python -m pytest tests -q` passes
- `flask --app run:app seed --reset` works
- docs match actual behavior

## Recommended Delivery Order

The safest high-level sequence is:

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 5
7. Phase 6
8. Phase 7

## Practical PR Breakdown

To keep the work reviewable, the implementation can be split into these PR-sized chunks:

1. model refactor + migration
2. team and roster management
3. tournament creation from existing teams
4. match creation and scheduling
5. score-entry restrictions and player validation
6. standings/dashboard/query cleanup
7. seed/test/doc alignment

## Risks and Dependencies

### Highest-risk area

The highest-risk change is moving from tournament-owned teams to reusable teams.
That change affects:

- schema
- standings
- tests
- seed data
- dashboard queries
- tournament detail rendering

### Main dependency chain

- match creation depends on tournament team registration
- roster-safe score entry depends on team roster management
- dashboard correctness depends on standings refactor

Because of this, starting from UI work before the model refactor would create avoidable rework.

## Definition of Done

The V2 implementation is complete when:

- teams are reusable global entities
- players are managed through team rosters
- tournaments select existing teams
- matches can be created under tournaments
- score entry only uses existing roster players
- standings are derived through tournament-specific participation records
- dashboard and public pages still work correctly
- tests, seed data, and documentation are aligned with the new behavior
