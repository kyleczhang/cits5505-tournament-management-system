# Frontend Implementation Plan — Checkpoint 2

This document records the plan that was followed to build the Checkpoint 2 frontend prototype for **CRIKTRACK — Cricket Tournament Management System**. It is intended both as a record of what was done and as a blueprint for converting the static prototype into a Flask/Jinja2 application in Checkpoint 3.

---

## 1. Goals

1. Deliver all 13 pages listed in `checkpoint-2-doc.md`.
2. Satisfy the Checkpoint 2 brief (`checkpoint-2-application-planning.md`) — HTML/CSS only, no Flask backend yet.
3. Anticipate the full project rubric (`project-description-and-rubrics.md`): wide-ranging HTML elements, custom CSS with responsive layout, valid JS with DOM manipulation/AJAX patterns, accessibility, good navigation, and a clear design identity.
4. Use the `ui-ux-pro-max` skill to derive a professional, cohesive design system.

---

## 2. Design System

Derived by running `ui-ux-pro-max` with the query `"sports tournament stats leaderboard dashboard professional"`, then adapted for a cricket context.

| Token            | Value                                   | Purpose                              |
| ---------------- | --------------------------------------- | ------------------------------------ |
| `--ctm-primary`  | `#0F766E` (teal-700)                    | Cricket field / brand                |
| `--ctm-accent`   | `#F59E0B` (amber-500)                   | Championship gold / CTA highlight    |
| `--ctm-cta`      | `#16A34A` (green-600)                   | Confirmation actions                 |
| `--ctm-bg`       | `#F8FAFC` (slate-50)                    | Page background                      |
| `--ctm-text`     | `#0F172A` (slate-900)                   | Body text (≥ 7:1 contrast)           |
| `--ctm-muted`    | `#475569` (slate-600)                   | Secondary text (≥ 4.5:1 contrast)    |
| `--ctm-border`   | `#E2E8F0` (slate-200)                   | Card and table borders               |

- **Typography:** Bebas Neue (display headings — sporty feel); Fira Sans 300/400/500/600/700 (body, UI, tables).
- **Icons:** inline SVG only (Heroicons/Lucide style). No emoji icons.
- **Radius scale:** `6 / 12 / 20 px`.
- **Shadow scale:** `sm` (1px hairline) → default (4px 12px) → `lg` (16px 40px).
- **Motion:** 150–300 ms `ease` transitions on colour, shadow, transform. `prefers-reduced-motion` disables all animation.
- **Anti-patterns avoided:** static content, emoji icons, layout-shifting hover states, `bg-white/10` glass cards, `gray-400` body text.

---

## 3. Technology Choices

| Concern              | Decision                                                        |
| -------------------- | --------------------------------------------------------------- |
| CSS framework        | Bootstrap 5.3 (loaded from jsDelivr CDN)                        |
| Custom styling       | One hand-written `css/styles.css` (~470 lines) over Bootstrap   |
| JavaScript           | Vanilla ES5-safe JS, no build step                              |
| Fonts                | Google Fonts (`Bebas Neue`, `Fira Sans`), preconnected          |
| Icons                | Inline SVG paths (no icon library dependency)                   |
| Mock data            | Global `window.CTM_MOCK` object in `js/mockdata.js`             |
| Shared layout        | Runtime `outerHTML` injection in `js/layout.js` (no SSR yet)    |
| Maps                 | Google Maps JavaScript API, async-loaded with env-injected key  |
| Live cricket data    | CricketData.org free tier (100 k hits/hour), proxied via Flask  |
| Roles & comments     | `User.role` enum (`organizer` / `user`) + per-match `Comment`   |

Reason: static HTML matches the Checkpoint 2 brief ("do not start implementing the back-end"), and a single-file CSS and no build step keep the prototype easy for every team member to open and edit.

---

## 4. Page List

| #  | Page                  | File                      | Key UI elements                                             |
| -- | --------------------- | ------------------------- | ----------------------------------------------------------- |
| 1  | Landing               | `index.html`              | Hero, feature grid, stats strip, CTA card                   |
| 2  | Sign Up               | `register.html`           | Auth card, 4 fields, password rules, terms checkbox         |
| 3  | Log In                | `login.html`              | Auth card, 2 fields, "remember me", forgot link             |
| 4  | Dashboard             | `dashboard.html`          | 4 stat cards, "my tournaments" grid, upcoming + results     |
| 5  | Create Tournament     | `tournaments-create.html` | Form (name/date/format/size), dynamic team rows             |
| 6  | Tournament Detail     | `tournament-detail.html`  | Hero, pill-tabs, Google Map venue marker, comments feed     |
| 7  | Match Scorecard       | `match-scorecard.html`    | Header, batting/bowling tables, venue map, comments feed    |
| 8  | Enter / Edit Results  | `match-record.html`       | Tabbed form, dynamic batter/bowler rows, winner + margin    |
| 9  | Player Stats          | `player-stats.html`       | Header, 4 summary cards, match-by-match table, bar chart    |
| 10 | Search Tournaments    | `tournaments-list.html`   | Search input + status filter pills, paginated card grid     |
| 11 | Public Tournament     | `tournament-public.html`  | Minimal nav, standings, live-score widget, sign-up CTA      |
| 12 | User Profile          | `profile.html`            | Avatar header, organiser stats, tournament history          |
| 13 | Edit Profile          | `profile-edit.html`       | Avatar upload, name/email/location/bio form                 |

---

## 5. Shared Conventions

Every page follows the same skeleton so conversion to Jinja2 is trivial:

```html
<head>
  <!-- meta, Bootstrap CSS, Google Fonts, css/styles.css -->
</head>
<body>
  <a href="#main" class="skip-link">Skip to main content</a>
  <div data-layout="nav"></div>           <!-- → {% include "partials/nav.html" %} -->
  <main id="main"> … page-specific content … </main>
  <div data-layout="footer"></div>        <!-- → {% include "partials/footer.html" %} -->
  <!-- Bootstrap JS bundle, layout.js, mockdata.js, main.js -->
</body>
```

- `layout.js` swaps the two placeholder `<div>`s for the real navbar and footer so every page stays in sync without a templating engine.
- The active nav link is highlighted via `data-page` attributes matched against `location.pathname`.
- A custom `showToast()` helper provides consistent post-submit feedback.

---

## 6. JavaScript Modules

The client JS is split into small, single-purpose files so the Flask migration can delete or rewrite them one by one. Load order (every page, in this exact sequence) is documented in Section 16.1.

### 6.1 `js/main.js` — shared interactivity

1. **Nav active state** — matches current filename.
2. **Form validation** — on any form with `data-ctm-validate`:
   - blur-based field validation (required, email regex, ≥ 8-char password).
   - submit-time password-confirm matching.
   - `aria-invalid="true"` + `role="alert"` error hints for screen readers.
   - simulated async submit: spinner → toast → optional `data-redirect` URL.
3. **Tournament filter** (list page) — live search + status filter pills show/hide cards.
4. **Dynamic rows** — `data-add-row` / `data-remove-row` / `data-row-template` pattern lets "add another batter / bowler / team" buttons clone a hidden template row.
5. **Share link** — `data-share` buttons copy the URL via `navigator.clipboard` and surface a toast.
6. Exposes `window.ctmToast(message)` for other modules.

### 6.2 `js/config.js` — runtime config

Exports `window.CTM_CONFIG` with:

- `googleMapsApiKey` (empty → maps.js renders OSM fallback; set → upgrades to Google Maps JS API)
- `liveFeedEndpoint` (default `/api/live/matches` — the future Flask proxy path)
- `liveFeedPollMs` (default 30 000)

In Checkpoint 3 this file is replaced by a Jinja-rendered inline `<script>` block in `base.html` (see Section 16.3).

### 6.3 `js/roles.js` — role gating + demo switcher

- Reads stored role from `localStorage` (key `ctm_active_role`), falls back to `CTM_MOCK.currentUser.role`, writes it to `<body data-ctm-role="…">`.
- Mirrors the active role back onto `CTM_MOCK.currentUser` (swapping from `CTM_MOCK.demoUsers`) so other modules see a consistent "signed-in user".
- Renders a fixed bottom-right **demo switcher** (`.ctm-role-switcher`) — **Checkpoint 2 only**, deleted in Checkpoint 3.
- Fires a `ctm:rolechange` CustomEvent so comments.js can refresh the "commenting as" header.
- Exposes `window.ctmRoles.current()` and `window.ctmRoles.set(role)`.

### 6.4 `js/maps.js` — venue map renderer

- Scans the page for `<div class="ctm-map-frame" data-ctm-map data-lat data-lng data-label>` blocks.
- If `CTM_CONFIG.googleMapsApiKey` is set, lazy-loads the Google Maps JS API once and draws a marker + InfoWindow.
- Otherwise renders an OpenStreetMap `<iframe>` as a no-key fallback.
- Writes a "View on Google Maps / OpenStreetMap →" attribution link into the adjacent `.ctm-map-provider` element.

### 6.5 `js/comments.js` — comment feed

- Scans the page for `<section data-ctm-comments data-match-id|data-tournament-id>`.
- Renders comments from `CTM_MOCK.comments`, filtered by the id attribute, sorted `createdAt desc`.
- Organizer comments carry `<span class="ctm-badge-organizer">Organizer</span>` and a gold left-border (`.ctm-comment-card.is-organizer`).
- Submit handler validates ≤ 500 chars, prepends to `CTM_MOCK.comments` in-memory (no backend yet), fires `ctmToast()`.
- Updates the "commenting as" header on `ctm:rolechange`.

### 6.6 `js/livefeed.js` — CricketData.org proxy client

- Scans the page for `<div data-ctm-livefeed>`.
- `fetch(CTM_CONFIG.liveFeedEndpoint)` every `liveFeedPollMs`; on any error falls back to `CTM_MOCK.liveFeed`.
- Renders a dark "Live cricket" widget with team, score, status, and attribution ("Data: CricketData.org" or "sample — backend proxy pending").
- The payload shape matches CricketData.org's `/currentMatches` response 1:1 (see §13.2), so the Flask proxy can be a straight pass-through.

### 6.7 `js/layout.js` — nav + footer injection

Injects the shared navbar and footer via `outerHTML`. Kept only until Checkpoint 3 `partials/nav.html` + `partials/footer.html` exist; at that point the file is deleted. The "Create" nav item carries `data-role-gate="organizer"`.

### 6.8 `js/mockdata.js` — fixtures

`window.CTM_MOCK` holds every object the UI needs — see Section 9. In Checkpoint 3 these fixtures stay for early Selenium tests and are progressively replaced by real Jinja context.

---

## 7. Accessibility Checklist

- [x] Skip-to-content link on every page
- [x] Every form input has a visible `<label for>` (no placeholder-only inputs)
- [x] Error messages use `aria-live="polite"` and `role="alert"`
- [x] Icon-only buttons have `aria-label`
- [x] Visible focus ring (3 px teal outline) on all interactive elements
- [x] Colour contrast ≥ 4.5:1 for text, ≥ 7:1 for body (`#0F172A` on `#F8FAFC`)
- [x] Colour is not the sole status indicator (status badges carry text labels)
- [x] `prefers-reduced-motion` disables animations
- [x] Breadcrumb navigation on nested pages
- [x] Valid semantic HTML (`main`, `nav`, `article`, `section`, `aside` via cards)

---

## 8. Responsive Strategy

- Mobile-first via Bootstrap grid (`col-` + `col-md-` + `col-lg-`).
- `match-row` grid collapses from 3 columns to 1 below 576 px.
- Auth card adapts padding below 768 px.
- Hero, scorecard header, and section padding shrink below 768 px.
- Tested at 375 px, 768 px, 1024 px, 1440 px.

---

## 9. Mock Data

All dynamic content lives in `js/mockdata.js` under `window.CTM_MOCK`:

- `currentUser` — logged-in user profile, including `role: 'organizer' | 'user'`
- `summary` — dashboard stat values
- `tournaments[]` — list used by dashboard & tournaments list
- `tournament` — detail page (standings, fixtures, top performers, `venue: {name, address, lat, lng}`)
- `match` — full scorecard (two innings, batting + bowling, `venue`, `comments[]`)
- `player` — per-player aggregate + match-by-match breakdown
- `comments[]` — `{ id, matchId, author, role, body, createdAt }`, used to seed comment feed
- `liveFeed` — sample payload shape matching the CricketData.org `currentMatches` endpoint, so the UI can be built against a realistic response before the backend proxy exists

When we wire up the Flask backend, each of these objects maps 1:1 to a Jinja context variable or an AJAX JSON response.

---

## 10. Task Split (per Checkpoint 2 Doc)

| Member              | Pages                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------- |
| Hafiz Zeeshan Ahmad | Landing, Dashboard, Search Tournaments, Public Tournament                                   |
| Leon Nel            | Create Tournament, Tournament Detail (fixtures/points/stats), Enter / Edit Results          |
| Cheng Zhang         | Sign Up, Log In, Match Scorecard, Player Stats, User Profile, Edit Profile                  |

---

## 11. How to Run

```bash
cd frontend
python3 -m http.server 8000
# Open http://localhost:8000/index.html
```

Or double-click `frontend/index.html` to open directly in the browser (all assets use relative paths).

Smoke-tested: all 13 pages and all static assets (`css/`, `js/`) return HTTP 200 under `python3 -m http.server`.

---

## 12. Checkpoint 3 Migration Plan

The prototype is designed to drop into a Flask/Jinja2 project with minimal rework.

### 12.1 Target repo structure

```
app/
├── __init__.py          # Flask app factory, db.init_app, blueprint registration
├── models.py            # SQLAlchemy models: User (with role enum), Tournament,
│                        #   Team, Player, Match, Innings, BattingEntry,
│                        #   BowlingEntry, Comment, Venue
├── auth/
│   ├── routes.py        # /register, /login, /logout
│   └── forms.py         # Flask-WTF RegisterForm, LoginForm (CSRF-protected)
├── tournaments/
│   ├── routes.py        # CRUD + /tournaments/<id>, /tournaments/<id>/share
│   └── forms.py
├── matches/
│   └── routes.py        # /matches/<id>, /matches/<id>/record (AJAX endpoints)
├── comments/
│   └── routes.py        # POST /matches/<id>/comments, GET /matches/<id>/comments
├── integrations/
│   ├── maps.py          # server-side geocoding helper (Google Maps Geocoding)
│   └── live_cricket.py  # CricketData.org proxy + 30 s cache (hides API key)
├── users/
│   └── routes.py        # /users/<id>, /profile/edit
├── templates/
│   ├── base.html                       ← wraps nav + footer partials
│   ├── partials/{nav,footer}.html      ← from js/layout.js NAV_HTML / FOOTER_HTML
│   ├── landing.html                    ← from index.html
│   ├── auth/{register,login}.html
│   ├── dashboard.html
│   ├── tournaments/{create,list,detail,public}.html
│   ├── matches/{scorecard,record}.html
│   └── users/{profile,profile_edit,player_stats}.html
├── static/
│   ├── css/styles.css                  ← unchanged
│   └── js/main.js                      ← mock AJAX replaced with real fetch()
├── tests/
│   ├── test_auth.py  test_tournaments.py  test_matches.py  (≥ 5 pytest units)
│   └── selenium/     (≥ 5 live-server Selenium tests)
└── run.py
```

### 12.2 Migration steps (in order)

1. **Scaffold Flask app factory** with `SECRET_KEY` in `.env`, loaded via `python-dotenv`.
2. **Extract partials** — copy `NAV_HTML` / `FOOTER_HTML` strings out of `layout.js` into `templates/partials/nav.html` and `footer.html`. Create `base.html` that renders them and a `{% block content %}`.
3. **Convert each page** to a Jinja template extending `base.html`. Replace hard-coded mock values with `{{ }}` expressions driven by a view's context.
4. **Delete `layout.js`** once partials are in place; keep `main.js` (its DOM logic still applies).
5. **Models + migrations** — start with `User`, `Tournament`, `Team`, `Player`, then `Match`, `Innings`, `BattingEntry`, `BowlingEntry`. Use Flask-Migrate (Alembic) for migrations — rubric explicitly mentions evidence of DB migrations.
6. **Auth** — Flask-Login for sessions, `werkzeug.security.generate_password_hash` (PBKDF2/scrypt) for salted hashes, Flask-WTF CSRF tokens on every form.
7. **Replace mock submit flow** — swap the "fake spinner + toast" block in `main.js` for a real `fetch(url, {method:'POST', body:formData})` that reads CSRF token from a meta tag and posts JSON to the Flask endpoint.
8. **AJAX endpoints** — Enter/Edit Results page posts batter/bowler rows as JSON; Tournament Detail tabs lazy-load fixtures/standings via `fetch`.
9. **Testing**:
   - pytest: registration validation, password hashing, tournament creation, fixture generation algorithm, points-table/NRR calculation.
   - Selenium: sign-up flow, log-in flow, create tournament, record match result, view public share link without being logged in, search/filter.
10. **Security hardening** — Flask-WTF CSRF, HttpOnly + Secure session cookies, config loaded from env vars, no secrets in repo, CSP header allowing only the CDNs we use.
11. **Roles** — add `role` column to `User` (enum: `organizer`, `user`, default `user`). Implement `@require_role('organizer')` decorator used on tournament create/edit and match record routes. Organizer sign-up is gated by an invite code stored in `.env`; regular sign-up always creates a `user`.
12. **Comments** — `Comment(id, match_id, user_id, body, created_at)`. POST endpoint validates length (≤ 500 chars) and CSRF. GET returns JSON list ordered by `created_at desc`, each entry carrying `author.role` so the frontend can render the organizer badge.
13. **External integrations** —
    - Google Maps: key in `GOOGLE_MAPS_API_KEY`, injected into `base.html` via `{{ config['GOOGLE_MAPS_API_KEY'] }}`. Geocode the venue address once on tournament create (server-side), persist `lat`/`lng` on `Venue`, and render a Maps JS marker on tournament-detail + match-scorecard.
    - CricketData.org: key in `CRICKETDATA_API_KEY`, never sent to the browser. Flask endpoint `/api/live/<external_match_id>` wraps the upstream call with a 30 s in-memory TTL cache to stay within the free-tier quota. Public tournament page polls this endpoint from JS.

### 12.3 What stays unchanged

- `css/styles.css` — every class is framework-agnostic.
- `js/main.js` — form validation, row adder, share, toast all continue to work.
- `js/mockdata.js` — kept as fixtures for early Selenium tests until real DB seeds replace it.
- All semantic HTML inside each `<main>` block.

---

## 13. External Integrations

### 13.1 Google Maps (venue display)

- **What it does:** every tournament has a `Venue { name, address, lat, lng }`. On tournament-detail and match-scorecard we render a map centred on the venue with a single marker + InfoWindow showing the venue name.
- **Shipped today (Checkpoint 2):** `js/maps.js` auto-upgrades between two backends based on `CTM_CONFIG.googleMapsApiKey`:
    - **key empty** (prototype default) → OpenStreetMap `<iframe>` fallback, no billing account needed. This is what the current prototype renders.
    - **key set** → Google Maps JavaScript API lazy-loaded once per page, then marker + InfoWindow drawn on the same `<div class="ctm-map-frame">`. No template change required to switch.
- **DOM contract:** pages drop a single block in; nothing page-specific to JS:

  ```html
  <div class="ctm-map">
    <div class="ctm-map-header">…venue name + address…</div>
    <div class="ctm-map-frame"
         data-ctm-map
         data-lat="{{ venue.lat }}"
         data-lng="{{ venue.lng }}"
         data-label="{{ venue.name }}"></div>
    <div class="ctm-map-provider"></div>
  </div>
  ```

- **Key handling (Checkpoint 3):** `GOOGLE_MAPS_API_KEY` lives in `.env`; `base.html` injects it into `window.CTM_CONFIG.googleMapsApiKey` via Jinja. The browser-shipped key should be HTTP-referrer restricted so the marker rendering is safe; the Geocoding API is only called from the server (see below).
- **Geocoding:** run once, server-side, at tournament creation time — free-text address → `(lat, lng)` via the Maps Geocoding API. We persist the coordinates on `Venue` so no client-side geocoding ever hits the quota.
- **Accessibility:** the map is decorative; the venue name and address remain as readable text above it so screen readers and no-JS users still get the location.

### 13.2 Live cricket data (external public API)

We surveyed the main public providers:

| Provider                                | Free tier                    | Notes                                                                |
| --------------------------------------- | ---------------------------- | -------------------------------------------------------------------- |
| **CricketData.org** (CricAPI successor) | 100 000 hits / hour, no card | JSON endpoints for live matches, fixtures, player stats. **Chosen.** |
| Roanuz Cricket API                      | Trial only, then paid        | High quality, ball-by-ball, IPL 2026 coverage — overkill for us.     |
| Entity Sport                            | Paid                         | Similar feature set to Roanuz.                                       |
| Sportmonks Cricket                      | 14-day trial                 | Commercial, REST + webhooks.                                         |
| RapidAPI cricket collections            | Varies per listing           | Unofficial scrapers of Cricbuzz/ESPN, reliability risk.              |

**Why CricketData.org:** free tier is generous enough for a class project, signup is email-only, JSON is straightforward, and the endpoints (`/currentMatches`, `/match_info`, `/match_scorecard`) map directly onto our data shapes.

**Integration shape:**

1. `integrations/live_cricket.py` wraps the upstream in a thin client (`get_current_matches()`, `get_match_info(id)`).
2. Responses are cached in-process for 30 seconds (`functools.lru_cache` + a timestamp, or `Flask-Caching` if we add it) so repeated polling does not burn quota.
3. Flask exposes `/api/live/matches` and `/api/live/match/<external_id>` as JSON proxies. The API key is **never** shipped to the browser.
4. The public tournament page polls `/api/live/matches` every `CTM_CONFIG.liveFeedPollMs` (default 30 s) via `fetch()`; JS renders a live-score strip at the top.
5. If the upstream returns 429 or errors, we degrade gracefully to "Live feed unavailable — showing last cached result at HH:MM".

**Shipped today (Checkpoint 2):** `js/livefeed.js` already does the fetch + poll + fallback dance:

- `fetch(CTM_CONFIG.liveFeedEndpoint)` on load, then every `liveFeedPollMs`.
- On any non-200 / network error → read `CTM_MOCK.liveFeed` instead and badge the widget with "sample — backend proxy pending".
- On success → render the upstream payload verbatim and badge with "Data: CricketData.org · updated HH:MM:SS".
- The sample payload in `CTM_MOCK.liveFeed` is shaped identically to the real `/currentMatches` response, so once Flask returns the upstream JSON untouched the UI stops showing the "sample" badge automatically — zero client changes needed.

### 13.3 Key management

Both keys go in `.env` (gitignored) and are loaded at app init via `python-dotenv`. `config.py` reads them into `app.config`. Checked into the repo: `.env.example` listing the variable names with empty values so teammates know what to fill in.

---

## 14. Roles & Comments

### 14.1 Two user roles

| Capability                              | `organizer` | `user` |
| --------------------------------------- | :---------: | :----: |
| View tournaments, fixtures, scorecards  | ✅          | ✅     |
| Create / edit a tournament              | ✅          | ❌     |
| Add / edit teams, players, venues       | ✅          | ❌     |
| Enter or edit match results             | ✅          | ❌     |
| Post a comment on a match               | ✅          | ✅     |
| Edit or delete **own** comment          | ✅          | ✅     |
| Delete **any** comment on own tournament| ✅          | ❌     |

- **Sign-up:** default role is `user`. To register as an organizer the user enters an invite code on `register.html` (code lives in `.env` as `ORGANIZER_INVITE_CODE`). This keeps the checkpoint demo simple while still modelling a meaningful authz boundary.
- **Frontend gating:** `currentUser.role` drives template conditionals — the "Create Tournament" CTA, the "Edit Results" button and the create/edit form entry points render only for organizers. Non-organizers see read-only pages.
- **Backend gating:** `@require_role('organizer')` decorator on all write routes. Unauthorised requests get a 403 + flash redirect to `/dashboard`. This is the real authority — the hidden buttons are only a UX nicety.

### 14.2 Comments on match pages

- **Model:** `Comment(id, match_id FK, user_id FK, body VARCHAR(500), created_at)`.
- **Placement:** a `<section class="ctm-comments">` block at the bottom of `match-scorecard.html` (and mirrored on `tournament-detail.html` scoped to the active match).
- **Submit:** a textarea + submit button, Flask-WTF CSRF token, POST to `/matches/<id>/comments`. Client-side validation caps the body at 500 chars; server re-validates.
- **Render:** most recent first; each item shows avatar, author name, relative timestamp, and body. Long bodies truncate with "show more".
- **Organizer badge:** if `comment.author.role == 'organizer'`, render `<span class="ctm-badge ctm-badge-organizer">Organizer</span>` next to the author name, plus a subtle 2-px accent-gold left border on the card. Non-organizer comments have no badge and a plain border.
- **Accessibility:** the badge carries a visible text label ("Organizer"), not a colour-only cue; the comment list is a `<ul>` of `<article>` elements with `aria-label="Comment by {name}"`.
- **Empty state:** "Be the first to comment" + disabled submit button if not logged in, with a "Log in to comment" link.

### 14.3 Prototype scope (Checkpoint 2)

What's actually wired today:

- **Two demo personas** — `CTM_MOCK.demoUsers.organizer` (Cheng Zhang) and `CTM_MOCK.demoUsers.user` (Priya Menon). The active role is persisted in `localStorage.ctm_active_role`.
- **Role propagation** — `js/roles.js` writes the active role onto `<body data-ctm-role="organizer|user">` and mirrors the matching persona into `CTM_MOCK.currentUser` so comments.js picks it up as the author.
- **Gating mechanism** — any element marked `data-role-gate="organizer"` is hidden by the CSS rule `body[data-ctm-role='user'] [data-role-gate='organizer']{display:none!important}`. Currently applied to:
    - Nav "Create" link ([js/layout.js](js/layout.js))
    - Dashboard "Create tournament" CTA + dashed "Create a new tournament" card ([dashboard.html](dashboard.html))
    - Tournaments list "+ New tournament" button ([tournaments-list.html](tournaments-list.html))
    - Tournament detail "Enter result" button ([tournament-detail.html](tournament-detail.html))
    - Match scorecard "Edit result" button ([match-scorecard.html](match-scorecard.html))
- **Demo switcher** — a fixed bottom-right pill (`.ctm-role-switcher`) with "Organizer | User" buttons. Checkpoint 2 only. It is the *entire* replacement for not having a real login system yet; deleted when Flask-Login lands (see §16.2).
- **Seeded comments** — `CTM_MOCK.comments[]` contains one organizer comment (Cheng) and two user comments (Priya, Daniel) on match 501 so the badge styling and permission gating are reviewable without clicking anything.

---

## 15. Rubric Cross-Check

| Rubric criterion                                    | Where it is already addressed (frontend)                                                |
| --------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Wide range of HTML elements                         | `nav`, `main`, `section`, `article`, `aside`, `table`, `form`, `details`, `breadcrumb`  |
| Jinja templates                                     | Planned — `base.html` + 13 page templates (Section 12)                                  |
| Custom CSS selectors                                | ~470 lines of custom CSS, 40+ custom classes over Bootstrap                             |
| Responsive to screen size                           | Bootstrap grid + custom media queries at 575 / 768 / 1024                               |
| Valid JS with validation and DOM manipulation/AJAX  | Form validation, dynamic row adder, filter/search, clipboard share                      |
| Well-organised Flask code                           | Planned — blueprint-per-feature layout (Section 12.1)                                   |
| Data models + migrations                            | Planned — 8 models + Flask-Migrate (Section 12.2)                                       |
| 5+ unit tests + 5+ Selenium tests                   | Planned — test plan in Section 12.2 step 9                                              |
| Salted password hashes                              | Planned — `werkzeug.security.generate_password_hash` (Section 12.2 step 6)              |
| CSRF tokens                                         | Planned — Flask-WTF on every form (Section 12.2 step 6)                                 |
| Environment variables in config                     | Planned — `.env` + `python-dotenv`, never committed                                     |
| Engaging, effective, intuitive design               | Design system, navigation, accessibility, responsive — all above                        |
| Two-role authorization (organizer / user)           | Planned — `User.role` enum + `@require_role` decorator (Section 14)                     |
| External public API integration                     | Planned — CricketData.org live-score proxy with caching (Section 13.2)                  |
| Third-party map embed for venues                    | Planned — Google Maps JS API with persisted geocoded lat/lng (Section 13.1)             |
| Comment system with organizer badge                 | Planned — per-match `Comment` model + badge styling (Section 14.2)                      |

---

## 16. Backend Integration Contract

This section is the checklist for the Checkpoint 3 developer. It records the exact hooks the shipped frontend expects so the Flask side can be written against a stable target. Following this contract means `css/styles.css`, `js/main.js`, `js/maps.js`, `js/comments.js`, `js/livefeed.js` and every HTML `<main>` block can be dropped into Jinja templates **without modification** — only `js/config.js`, `js/roles.js` and `js/layout.js` need to change or disappear.

### 16.1 Script loading order

Every page (via `templates/base.html`) must load scripts in this exact order — globals must exist before consumers run:

1. Bootstrap JS bundle (CDN)
2. Inlined `<script>` that writes `window.CTM_CONFIG` (replaces `js/config.js` — see §16.3)
3. `js/mockdata.js` — keep during early migration; remove page-by-page as real data arrives
4. `js/layout.js` — delete entirely once `partials/nav.html` + `partials/footer.html` exist
5. `js/roles.js` — replace with the slim 3-line version from §16.2, or delete and let Jinja set `<body data-ctm-role>` directly
6. `js/maps.js`, `js/comments.js`, `js/livefeed.js` — only include on pages that need them
7. `js/main.js`

### 16.2 Role injection (replaces the demo switcher)

Set the role once, server-side, in `base.html`:

```jinja
<body data-ctm-role="{{ current_user.role if current_user.is_authenticated else 'user' }}">
```

That single attribute is the entire API. The existing CSS rule
`body[data-ctm-role='user'] [data-role-gate='organizer']{display:none!important}`
handles the rest.

What to remove from `js/roles.js`:

- `renderSwitcher()`, `updateSwitcherState()` and the `bootstrap()` calls that append the pill
- The `localStorage` read/write (real sessions replace it)
- The `CTM_MOCK.demoUsers` mirroring (real `current_user` replaces it)

What to keep: the `ctm:rolechange` CustomEvent dispatch is unused once real sessions land and can be deleted.

Also remove the `.ctm-role-switcher` block from `css/styles.css`.

### 16.3 `CTM_CONFIG` injection (replaces `js/config.js`)

Render this inline in `base.html`:

```jinja
<script>
  window.CTM_CONFIG = {
    googleMapsApiKey: {{ config['GOOGLE_MAPS_API_KEY']|tojson }},
    liveFeedEndpoint: "{{ url_for('live.matches') }}",
    liveFeedPollMs: 30000
  };
</script>
```

Delete `js/config.js`. `js/maps.js` detects the populated key and upgrades every `[data-ctm-map]` from OSM to Google Maps with no template changes.

### 16.4 Google Maps & venue DOM contract

Templates render exactly this block wherever a venue is shown — `js/maps.js` handles the rest:

```html
<div class="ctm-map">
  <div class="ctm-map-header">
    <svg …map-pin icon…></svg>
    <div>
      <div class="ctm-map-title">{{ venue.name }}</div>
      <div class="ctm-map-address">{{ venue.address }}</div>
    </div>
  </div>
  <div class="ctm-map-frame"
       data-ctm-map
       data-lat="{{ venue.lat }}"
       data-lng="{{ venue.lng }}"
       data-label="{{ venue.name }}"></div>
  <div class="ctm-map-provider"></div>
</div>
```

Server-side rules:

- On tournament/venue create: POST handler calls Google Maps Geocoding API once, persists `{name, address, lat, lng}` onto `Venue`, links it to the `Tournament` and (optionally per-match) the `Match`.
- If geocoding fails or `GOOGLE_MAPS_API_KEY` is not set, leave `lat`/`lng` NULL and wrap the `.ctm-map` block in `{% if venue.lat and venue.lng %}` so it gracefully hides.
- The key rendered into `CTM_CONFIG` should be a **browser-safe, HTTP-referrer-restricted** key. Geocoding (server-side) uses a separate unrestricted key read only from `os.environ` — never passed to the client.

### 16.5 Comments endpoint contract

`js/comments.js` currently reads `CTM_MOCK.comments` and appends in-memory. Replace the body of `renderList()` with a GET fetch and the form submit handler with a POST; both speak the same JSON shape.

**GET `/api/matches/<int:match_id>/comments`** → `200 OK`, body is a JSON array of:

```json
{
  "id": 9001,
  "matchId": 501,
  "tournamentId": 101,
  "authorId": 1,
  "authorName": "Cheng Zhang",
  "initials": "CZ",
  "role": "organizer",
  "body": "Great hitting from Aarav today.",
  "createdAt": "2026-04-12T20:05:00+08:00"
}
```

Ordering: newest first (`ORDER BY created_at DESC`). `role` must be one of `"organizer"` / `"user"` — that single field drives the organizer badge.

A matching GET endpoint exists for tournament-scoped comments: `/api/tournaments/<int:tournament_id>/comments`.

**POST `/api/matches/<int:match_id>/comments`** (CSRF-protected) → body `{"body":"…"}`, returns the created comment in the same shape above.

- `400` if body is empty or > 500 chars
- `401` if not logged in
- `403` if match does not allow comments (reserved for future moderation)

CSRF: the client reads the token from `<meta name="csrf-token" content="{{ csrf_token() }}">` in `base.html` and sends it in an `X-CSRFToken` header. Flask-WTF's global protection covers the POST.

### 16.6 Live cricket feed endpoint contract

**GET `/api/live/matches`** — pure pass-through proxy:

- Server calls CricketData.org `GET https://api.cricapi.com/v1/currentMatches?apikey=…&offset=0` using the key from `os.environ['CRICKETDATA_API_KEY']`.
- Response body is forwarded to the client verbatim (the shape already documented in `CTM_MOCK.liveFeed` — `{status, data:[…]}` with `teamInfo`, `score[]`, `status`, `venue`).
- Cache 30 s in-process; on cache hit return the stored payload with an `X-CTM-Cache: HIT` header (informational).
- On upstream 429 / 5xx / timeout: return the last successful cached payload with HTTP 200 and an `X-CTM-Stale: 1` header — `js/livefeed.js` will render it normally while the "sample" badge stays hidden.

### 16.7 Page wiring summary

Which backend endpoints each page needs:

| Page                     | Needs                                                                                                                                    |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `tournament-detail.html` | Jinja context for fixtures/standings/performers; `GET /api/tournaments/<id>/comments`; POST comment; venue block from `tournament.venue` |
| `match-scorecard.html`   | Jinja context for innings; `GET /api/matches/<id>/comments`; POST comment; venue block from `match.venue`                                |
| `tournament-public.html` | `GET /api/live/matches` (polled); no auth required; `data-ctm-role` forced to `user`                                                     |
| Every authenticated page | `current_user` for `<body data-ctm-role>` and the nav/CTA gating                                                                         |

### 16.8 What to delete when the backend lands

| Frontend artefact                         | Replaced by                                                       |
| ----------------------------------------- | ----------------------------------------------------------------- |
| `renderSwitcher()` in `js/roles.js`       | `<body data-ctm-role>` rendered by Jinja                          |
| `.ctm-role-switcher` CSS block            | (unused — delete)                                                 |
| `CTM_MOCK.demoUsers`                      | Flask-Login `current_user`                                        |
| `CTM_MOCK.currentUser` defaults           | Server-rendered user context                                      |
| In-memory comment append in `comments.js` | Real POST + re-render from GET                                    |
| `CTM_MOCK.liveFeed`                       | Still useful as an upstream-failure fallback — optional to remove |
| `js/config.js`                            | Inline `<script>` in `base.html`                                  |
| `js/layout.js`                            | `{% include 'partials/nav.html' %}` + footer partial              |
| Every hard-coded venue/team/score in HTML | `{{ }}` expressions from the view context                         |
