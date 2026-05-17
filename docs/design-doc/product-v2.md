# CRIKTRACK V2 Product Document

## 1. Product Goal

CRIKTRACK V2 is a cricket tournament management system for organizers.
It allows organizers to manage teams and player rosters first, then create tournaments, schedule matches, record results, and automatically generate standings and player statistics.

## 2. V2 Scope

CRIKTRACK V2 includes these core entities:

- `Tournament`: the competition
- `Team`: a participating team
- `Player`: a player belonging to a team
- `Match`: a single scheduled game between two teams

V2 does **not** require a separate `Fixture` model.

In product terms, `fixtures` simply means the collection of `Match` records under a `Tournament`.

## 3. User Roles

- `Organizer`
  - Creates and manages teams
  - Manages team rosters
  - Creates tournaments
  - Creates and manages matches
  - Records and edits match results

- `Fan/User`
  - Browses tournaments
  - Views scorecards
  - Views standings
  - Views player statistics
  - Follows tournaments, teams, and players

## 4. Core Business Concepts

- A `Team` is an independent entity in the system.
- A `Player` belongs to one `Team`.
- A `Tournament` is created by an organizer and contains multiple participating teams.
- A `Match` belongs to one `Tournament` and is played between two teams in that tournament.
- `Match` and its scorecard data are the source of truth.
- `Standings`, `player stats`, `recent results`, and dashboard summaries are all derived from match data.
- `Fixture` is a scheduling concept, not a separate data model in V2.

## 5. Core User Flow

1. The organizer creates one or more `Team` records.
2. The organizer manages each team's roster by adding, editing, or removing `Player` records.
3. The organizer creates a `Tournament`.
4. During tournament creation, the organizer selects participating teams from existing teams in the database.
5. The organizer creates matches for the tournament, either manually or through fixture generation.
6. Before a game starts, the `Match` status is `UPCOMING`.
7. When a game begins, the organizer changes the `Match` status to `LIVE`.
8. Live matches appear in the organizer dashboard under `Needs your attention`.
9. After the match ends, the organizer records the scorecard and result.
10. The system automatically recalculates standings, player statistics, recent results, and dashboard summaries.

## 6. Status Design

### Tournament Status

- `UPCOMING`
- `LIVE`
- `COMPLETED`

### Match Status

- `UPCOMING`
- `LIVE`
- `COMPLETED`

Use `LIVE` consistently in the product. Do not mix `LIVE` and `ONGOING`.

## 7. Functional Requirements

### Team Management

- Create team
- Edit team basic information
- Delete team
- View team roster

### Player Management

- Add players from the team roster page
- Edit player basic information
- Remove players from a team
- Do not use a player page as the main place to assign a player to a team

### Tournament Management

- Create tournament basic information
- Select participating teams from existing database records using a searchable selector
- Do not allow free-text team entry during tournament creation
- View tournament details
- View tournament matches, standings, and recent results

### Match Management

- Create matches for a tournament
- Each match must specify:
  - `team_a`
  - `team_b`
  - `scheduled_at`
  - optional `venue`
- The organizer can move a match from `UPCOMING` to `LIVE`
- The organizer can record or edit match results

### Scorecard and Result Recording

- Record:
  - toss winner
  - toss decision
  - innings
  - batting entries
  - bowling entries
  - winner
  - result text
- When recording a match, players must be selected only from the rosters of the two teams in that match
- The system must not create new players during score entry

### Derived Views

- Standings are automatically recalculated
- Player statistics are automatically aggregated
- Recent results are automatically generated
- Organizer dashboard summaries are automatically generated

## 8. Key Business Rules

- A tournament cannot be created without participating teams.
- Participating teams in a tournament must come from existing `Team` records.
- A match cannot be created without teams assigned to the tournament.
- Both teams in a match must belong to the same tournament.
- A player must belong to a team.
- During score entry, a player must come from `match.team_a.players` or `match.team_b.players`.
- Standings must never be edited manually.
- Standings must always be recalculated from completed matches.
- An organizer can only manage tournaments and related data that they own.
- Completed matches may be edited, but editing must trigger recalculation of standings and player statistics.

## 9. Recommended Pages

- `Teams List`
- `Team Detail / Team Roster Management`
- `Create Tournament`
- `Tournament Detail`
- `Create / Manage Tournament Matches`
- `Match Scorecard`
- `Record / Edit Match Result`
- `Organizer Dashboard`
- `Player Statistics Page`

## 10. Suggested Data Model for V2

### Team

- Basic team information
- Organizer ownership if required by the product rules

### Player

- `team_id`
- `name`
- `role`

### Tournament

- Basic tournament information
- `organiser_id`
- `status`

### Match

- `tournament_id`
- `team_a_id`
- `team_b_id`
- `scheduled_at`
- `status`
- `winner_id`
- `result_text`
- optional `venue_id`

## 11. What V2 Does Not Include

- Tournament-specific roster management
- Player transfer history
- Temporary loan players
- Registration deadlines
- Eligibility rules across tournaments
- Advanced competition structures such as groups, rounds, or brackets
- Creating new players while entering match results
- A separate `Fixture` model

## 12. V2 Success Criteria

CRIKTRACK V2 is successful if:

- Organizers can create teams first
- Organizers can manage player rosters through team pages
- Organizers can create tournaments by selecting existing teams
- Organizers can create matches for a tournament
- Organizers can record and edit match results
- The system automatically generates standings, player statistics, recent results, and organizer dashboard reminders
