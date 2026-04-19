# CRIKTRACK — Cricket Tournament Management System

A web application for creating and managing cricket tournaments. Organisers can set up fixtures (knockout, round-robin, or group stage), record detailed scorecards, track player statistics, and share tournament results with anyone via a public link.

Built for **CITS5505 (Agile Web Development) — Group Project 2026**.

## Team

| UWA ID   | Name                | GitHub Username |
| -------- | ------------------- | --------------- |
| 24237576 | Hafiz Zeeshan Ahmad | Armaanzee       |
| 24268801 | Leon Nel            | DemionNeo1      |
| 24878502 | Cheng Zhang         | kyleczhang      |

## Current Status — Checkpoint 2 (Frontend UI)

At this stage the repository contains the **frontend HTML/CSS/JS prototype only** — no Flask backend yet, per the Checkpoint 2 instructions. All data shown on the pages is mock data loaded from `frontend/js/mockdata.js`. The Flask/SQLAlchemy backend will be implemented in Checkpoint 3.

## Frontend — how to view the pages

Because the frontend is pure static HTML/CSS/JS, you can open the pages in a browser in two ways.

### Option 1: Open directly

```bash
open frontend/index.html          # macOS
xdg-open frontend/index.html      # Linux
start frontend/index.html         # Windows
```

### Option 2: Run a local static server (recommended)

Running a local server avoids any browser restrictions on `file://` URLs and more closely mirrors how Flask will serve the pages in Checkpoint 3.

```bash
cd frontend
python3 -m http.server 8000
```

Then visit <http://localhost:8000/index.html>.

## Pages

All 13 pages listed in the Checkpoint 2 planning document are implemented.

| #   | Page                  | File                         |
| --- | --------------------- | ---------------------------- |
| 1   | Landing               | `index.html`                 |
| 2   | Sign Up               | `register.html`              |
| 3   | Log In                | `login.html`                 |
| 4   | Dashboard             | `dashboard.html`             |
| 5   | Create Tournament     | `tournaments-create.html`    |
| 6   | Tournament Detail     | `tournament-detail.html`     |
| 7   | Match Scorecard       | `match-scorecard.html`       |
| 8   | Enter / Edit Results  | `match-record.html`          |
| 9   | Player Stats          | `player-stats.html`          |
| 10  | Search Tournaments    | `tournaments-list.html`      |
| 11  | Public Tournament     | `tournament-public.html`     |
| 12  | User Profile          | `profile.html`               |
| 13  | Edit Profile          | `profile-edit.html`          |

## Tech Stack

| Layer    | Technology                                   |
| -------- | -------------------------------------------- |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, jQuery |
| Backend  | Python, Flask, Jinja2 *(Checkpoint 3)*       |
| Database | SQLite via SQLAlchemy *(Checkpoint 3)*       |
| Testing  | pytest, Selenium *(Checkpoint 3)*            |

## Design Notes

- **Framework:** Bootstrap 5.3 (loaded from CDN).
- **Colour palette:** field-green (`#0F766E`) primary + championship-gold (`#F59E0B`) accent, slate text on off-white backgrounds.
- **Typography:** Bebas Neue for display headings (sporty feel); Fira Sans for body text.
- **Icons:** inline SVG only — no emoji icons.
- **Accessibility:** skip-to-content link, `aria-live` form errors, keyboard focus rings, 4.5:1+ contrast, `prefers-reduced-motion` respected.
- **Responsive:** tested at 375px, 768px, 1024px, 1440px breakpoints.
- **Mock AJAX:** forms validate on blur and show a loading spinner on submit before redirecting (see `frontend/js/main.js`).

## Running Tests

A comprehensive test suite (5+ pytest unit tests and 5+ Selenium tests) will be added in Checkpoint 3 alongside the Flask backend. Placeholder command:

```bash
# Planned for Checkpoint 3:
pytest tests/
```

## Project Structure

```
.
├── README.md
├── checkpoint-2-doc.md                     # Application planning document
├── checkpoint-2-application-planning.md    # Checkpoint 2 brief
├── project-description-and-rubrics.md      # Project rubric
└── frontend/
    ├── index.html                          # Landing page
    ├── register.html, login.html           # Auth
    ├── dashboard.html                      # Logged-in home
    ├── tournaments-create.html             # Create form
    ├── tournaments-list.html               # Browse + filter
    ├── tournament-detail.html              # Fixtures / standings / stats tabs
    ├── tournament-public.html              # Shareable read-only view
    ├── match-scorecard.html                # Full scorecard
    ├── match-record.html                   # Enter/edit result form
    ├── player-stats.html                   # Per-player stats
    ├── profile.html, profile-edit.html     # User profile
    ├── css/styles.css                      # Design system
    └── js/
        ├── layout.js                       # Shared navbar/footer injection
        ├── mockdata.js                     # Mock backend data
        └── main.js                         # Form validation, filters, toasts
```

## Team Organisation

- **Meetings:** Every Wednesday 12 PM – 2 PM, adjusted via When2Meet when needed.
- **Communication:** Microsoft Teams for day-to-day discussion; GitHub Issues and Pull Requests for task tracking and code review.
- **Workflow:** Each feature or bug fix is developed on its own branch and merged via Pull Request with at least one review from another team member.

### Frontend Task Allocation (Checkpoint 2)

| Member              | Pages                                                                                                         |
| ------------------- | ------------------------------------------------------------------------------------------------------------- |
| Hafiz Zeeshan Ahmad | Landing, Dashboard, Search Tournaments, Public Tournament                                                     |
| Leon Nel            | Create Tournament, Tournament Detail (fixtures/points/stats tabs), Enter / Edit Results                       |
| Cheng Zhang         | Sign Up, Log In, Match Scorecard, Player Stats, User Profile, Edit Profile                                    |
