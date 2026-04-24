# Checkpoint 2 Document

## 1 Application Overview

### 1.1 Purpose

The **Cricket Tournament Management System** is a web application that allows users to create and manage cricket tournaments, record match results, track player and team statistics, and share tournament outcomes with other users. It serves cricket enthusiasts, league organisers, and casual players who want a centralised platform to run tournaments and analyse performance.

### 1.2 Core Requirements

| Requirement | How It Is Met |
|---|---|
| Client-server architecture | Flask backend serving HTML templates to the browser; AJAX for dynamic updates |
| User login and logout | Registration and authentication system with secure password handling |
| Persistent data | SQLite + SQLAlchemy storing all user, tournament, and match data |
| View other users' data | Users can view shared tournaments, public leaderboards, and other users' match results |

### 1.3 CSS Framework

**Bootstrap 5**: We used Bootstrap 5 in our individual assignments so it is the framework everyone is most familiar with. Compared to writing vanilla HTML and CSS from scratch, Bootstrap provides a large set of ready-to-use components and a responsive grid system, it can speed up development significantly and gives pages a polished, consistent look with less effort.

## 2 User Stories

### 2.1 Account Management

1. **As a new user**, I want to sign up with my name, email, and password so that I can create and manage tournaments.
2. **As a registered user**, I want to log in to my account so that I can access my dashboard and tournaments.
3. **As a logged-in user**, I want to view and edit my profile (display name, avatar, bio) so that other users can learn about me.

### 2.2 Tournament Creation and Setup

1. **As a tournament organiser**, I want to create a new tournament by entering a name, start date, format (knockout, round-robin, or group stage), and number of teams so that I can set up a competition.
2. **As a tournament organiser**, I want to add teams and assign players to each team so that the tournament roster is complete before play begins.
3. **As a tournament organiser**, I want to generate a match schedule/fixture list automatically based on the tournament format so that all participants know when they play.

### 2.3 Match Results and Scoring

1. **As a tournament organiser**, I want to input match results including runs scored, wickets taken, overs bowled, and individual player performances so that the scorecard is recorded accurately.
2. **As a user**, I want to view a detailed match scorecard showing batting and bowling figures for both teams so that I can review how a match unfolded.

### 2.4 Statistics and Standings

1. **As a user**, I want to view a points table / leaderboard for any tournament so that I can see which teams are leading.
2. **As a user**, I want to view individual player statistics (total runs, batting average, total wickets, bowling average, strike rate) across a tournament so that I can identify top performers.

### 2.5 Discovery and Sharing

1. **As a user**, I want to search for tournaments by name, date, or status (upcoming, in progress, completed) so that I can find competitions I am interested in.
2. **As a user**, I want to share a tournament's results page via a unique link so that friends and other players can view the outcomes without needing an account.
3. **As a user**, I want to view a public tournament page (without logging in) when someone shares a link with me so that I can see results and stats easily.

## 3 Page List and Descriptions

| #   | Page                                                                          | Description                                                                                                                                                                                             |
| --- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Landing Page** (`/`)                                                        | Public-facing page explaining the app, with feature highlights and call-to-action buttons for Sign Up and Log In.                                                                                       |
| 2   | **Sign Up Page** (`/register`)                                                | Registration form (name, email, password, confirm password) with client-side validation and a link to Log In.                                                                                           |
| 3   | **Login Page** (`/login`)                                                     | Email and password login form with a link to Sign Up.                                                                                                                                                   |
| 4   | **Dashboard** (`/dashboard`)                                                  | Logged-in user's home — summary cards (my tournaments, upcoming matches, recent results), quick-action buttons (create tournament, browse tournaments).                                                 |
| 5   | **Create Tournament Page** (`/tournaments/create`)                            | Form to set up a new tournament: name, start date, format (knockout / round-robin / group stage), number of teams, team names, and player assignments.                                                  |
| 6   | **Tournament Detail Page** (`/tournaments/<id>`)                              | Overview of a single tournament with tabbed sections: fixtures list, points table (sorted by points and net run rate), and top performer statistics. Includes a share button to generate a public link. |
| 7   | **Match Scorecard Page** (`/tournaments/<id>/matches/<match_id>`)             | Detailed scorecard for one match — batting table, bowling table, innings summaries, and result. If the match has not been played, shows the scheduled date and teams.                                   |
| 8   | **Enter / Edit Results Page** (`/tournaments/<id>/matches/<match_id>/record`) | Form for the organiser to input or update match results: runs, wickets, overs per innings, and individual player performances. Uses AJAX for dynamic form sections.                                     |
| 9   | **Player Stats Page** (`/tournaments/<id>/players/<player_id>`)               | Aggregated statistics for a player within a tournament: total runs, batting average, total wickets, bowling average, strike rate, and match-by-match breakdown.                                         |
| 10  | **Search Tournaments Page** (`/tournaments`)                                  | Search bar with filters (name, date, status: upcoming / in progress / completed) and a paginated list of tournament cards.                                                                              |
| 11  | **Public Tournament Page** (`/tournaments/<id>/share`)                        | Shareable read-only view of a tournament's results and stats, accessible without logging in via a unique link.                                                                                          |
| 12  | **User Profile Page** (`/users/<id>`)                                         | Displays user details (name, avatar, bio) and their tournament history. When viewing your own profile, an Edit button links to the edit form.                                                           |
| 13  | **Edit Profile Page** (`/profile/edit`)                                       | Form to update display name, avatar, and bio. Save and cancel buttons.                                                                                                                                  |

## 4 Team Organisation

| UWA ID   | Name                | GitHub Username |
| -------- | ------------------- | --------------- |
| 24237576 | Hafiz Zeeshan Ahmad | Armaanzee       |
| 24268801 | Leon Nel            | DemionNeo1      |
| 24878502 | Cheng Zhang         | kyleczhang      |

- **Meetings:** Every Wednesday 12 PM – 2 PM, adjusted as needed via When2Meet.
- **Communication:** Microsoft Teams for day-to-day discussion; GitHub Issues and Pull Requests for task tracking and code review.
- **Workflow:** Each feature or bug fix is developed on its own branch and merged via Pull Request with at least one review from another team member.

### Frontend Task Allocation

| Member              | Pages                                                                                                          |
| ------------------- | -------------------------------------------------------------------------------------------------------------- |
| Hafiz Zeeshan Ahmad | Landing Page, Dashboard, Search Tournaments Page, Public Tournament Page                                       |
| Leon Nel            | Create Tournament Page, Tournament Detail Page (fixtures, points table, stats tabs), Enter / Edit Results Page |
| Cheng Zhang         | Sign Up Page, Login Page, Match Scorecard Page, Player Stats Page, User Profile Page, Edit Profile Page        |

## 5 Technology Stack

| Layer    | Technology                                   |
| -------- | -------------------------------------------- |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, jQuery |
| Backend  | Python, Flask, Jinja2                        |
| DB | SQLite via SQLAlchemy                        |
| Testing  | pytest, Selenium                             |
