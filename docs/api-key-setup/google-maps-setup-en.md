# CRIKTRACK Google Maps Setup Guide

This guide is based on the current code in this project. It is intended for local development and walks through how to configure Google Maps, obtain the required API keys, connect them to the codebase, and verify the behavior in the UI.

Applicable date: 2026-05-01
Project: `CRIKTRACK`
Recommended practice: prepare **two separate keys** for this project instead of using only one.

- `GOOGLE_MAPS_API_KEY`: used by the browser to load the Google Maps JavaScript API.
- `GOOGLE_MAPS_GEOCODING_API_KEY`: used by the Flask backend to convert venue addresses into coordinates.

Why two keys:

- the frontend key is exposed to the browser
- the backend geocoding key should stay server-side as much as possible
- the two keys need different security restrictions

## 1. Understand how Google Maps is used in this project

In this project, the Google Maps logic has two separate parts:

1. When a tournament is created and a venue address is provided, the backend calls the Geocoding API to convert the address into `lat/lng`.
2. When a venue is displayed, the frontend reads `lat/lng` and tries Google Maps first. If no browser key is configured, it falls back to OpenStreetMap.

Relevant code:

- Environment variable example: `app/.env.example`
- Config loading: `app/config.py`
- Frontend config injection: `app/criktrack/__init__.py`
- Server-side geocoding: `app/criktrack/integrations/geocoding.py`
- Tournament creation and coordinate persistence: `app/criktrack/tournaments/routes.py`
- Frontend map rendering: `app/criktrack/static/js/maps.js`

## 2. Create a Google Cloud project and enable billing

1. Open Google Maps Platform Getting Started:
   <https://developers.google.com/maps/get-started>
2. Sign in with your Google account.
3. Create a new Google Cloud project, or select an existing one.
4. Attach a billing account to that project.

Notes:

- Google Maps Platform requires a billing-enabled project before these APIs can be used normally.
- Without billing, Google Maps and Geocoding in this project will generally not work in a production-like way.

## 3. Enable the two APIs this project actually needs

Go to the API Library in Google Cloud Console and enable these APIs:

1. `Maps JavaScript API`
2. `Geocoding API`

Official links:

- Maps JavaScript API: <https://developers.google.com/maps/documentation/javascript>
- Geocoding API: <https://developers.google.com/maps/documentation/geocoding/get-api-key>

Do not enable a large set of unrelated APIs. This repository currently needs only these two.

## 4. Create the frontend browser API key

This corresponds to:

```env
GOOGLE_MAPS_API_KEY=
```

Steps:

1. Open the Google Maps Platform Credentials page.
2. Click `Create credentials`.
3. Choose `API key`.
4. After creation, rename it clearly, for example:
   `criktrack-browser-maps-key`
5. Open the key's edit page and configure restrictions.

Recommended restrictions:

1. Set `Application restrictions` to `HTTP referrers (web sites)`.
2. For local development, allow:
   - `http://localhost:5000/*`
   - `http://127.0.0.1:5000/*`
3. If you later deploy the project, add the production domains as well, for example:
   - `https://your-domain.example/*`
4. Set `API restrictions` to `Restrict key`.
5. Allow only `Maps JavaScript API`.

Why this setup:

- this key is injected into frontend pages, so it must be restricted by website origin
- limiting it to `Maps JavaScript API` reduces abuse risk if the key leaks

## 5. Create the backend geocoding API key

This corresponds to:

```env
GOOGLE_MAPS_GEOCODING_API_KEY=
```

Steps:

1. Create another `API key`.
2. Give it a clear name, for example:
   `criktrack-server-geocoding-key`
3. Open the key's edit page and configure restrictions.

Recommended restrictions:

1. Set `API restrictions` to `Restrict key`.
2. Allow only `Geocoding API`.
3. In a deployed environment, if you know your server's public IP, set `Application restrictions` to `IP addresses` and allow only that server IP.

Local development note:

- according to Google's docs, `IP addresses` restrictions for server keys do **not** support `localhost`
- for local development, the most practical approach is usually:
  - first restrict the key only to `Geocoding API`
  - add `IP addresses` restrictions later after deployment

Do not put this geocoding key into frontend config, because it should not be exposed to the browser.

## 6. Configure the keys in this project

This project reads configuration from `app/.env`. The logic already exists in `app/config.py`, so no Python logic changes are required.

### 6.1 Create `.env`

If you do not already have `.env`:

```bash
cd app
cp .env.example .env
```

### 6.2 Edit `app/.env`

Add these values:

```env
GOOGLE_MAPS_API_KEY=your_browser_maps_key
GOOGLE_MAPS_GEOCODING_API_KEY=your_backend_geocoding_key
```

Recommendations:

- do not hardcode keys in Python or JS files
- `GOOGLE_MAPS_API_KEY` will be exposed to the frontend, so it must be a browser-restricted key
- `GOOGLE_MAPS_GEOCODING_API_KEY` should exist only in backend environment variables

## 7. Understand how these keys take effect in code

You do not need to edit code here, but you should understand the data flow:

1. `app/config.py` reads:
   - `GOOGLE_MAPS_API_KEY`
   - `GOOGLE_MAPS_GEOCODING_API_KEY`
2. `app/criktrack/__init__.py` injects `GOOGLE_MAPS_API_KEY` into `window.CTM_CONFIG` in templates.
3. `app/criktrack/static/js/maps.js` checks `window.CTM_CONFIG.googleMapsApiKey`:
   - if present: load the Google Maps JavaScript API
   - if missing: fall back to OpenStreetMap
4. `app/criktrack/tournaments/routes.py` calls `geocode_address(...)` when a tournament is created.
5. `app/criktrack/integrations/geocoding.py` uses `GOOGLE_MAPS_GEOCODING_API_KEY` to call the Geocoding API and returns `(lat, lng)` on success.

## 8. Start the project

```bash
cd app
source .venv/bin/activate
flask --app run:app db upgrade
flask --app run:app run
```

Default address:

- <http://127.0.0.1:5000/>

## 9. Verify the behavior in the browser

One important detail:

- **geocoding is written to the database when the tournament is created**
- if an older venue was created before the geocoding key existed, its `lat/lng` may already be empty
- the safest verification method is: **configure the keys first, then create a new tournament with a venue address**

Suggested validation flow:

1. Open the home page and log in.
2. Use an organizer account and go to `Create tournament`.
3. Fill in:
   - Tournament name
   - at least two teams
   - `Venue name`
   - `Venue address`
4. Submit the form.
5. Open the tournament detail page.
6. Find the venue map section.

Expected results:

1. If both keys are configured correctly:
   - the venue is geocoded into coordinates
   - the page shows a Google Map
   - a `View on Google Maps` link appears
2. If only the geocoding key is configured, but the frontend maps key is missing:
   - the venue still gets coordinates
   - the page falls back to an OpenStreetMap iframe
3. If neither key is configured:
   - geocoding is skipped
   - the venue likely has no coordinates
   - the page will not show the full Google Maps experience

## 10. Quick troubleshooting

### Case 1: the map is still OpenStreetMap, not Google Maps

Check these first:

1. whether `GOOGLE_MAPS_API_KEY` is set in `app/.env`
2. whether the Flask process was restarted after `.env` changed
3. whether the browser key has the wrong referrer restriction
4. whether you are visiting `http://127.0.0.1:5000` while the key only allows `localhost:5000`

### Case 2: the venue has an address, but no map appears

Check these first:

1. whether the venue was created before the geocoding key was configured
2. whether `GOOGLE_MAPS_GEOCODING_API_KEY` is set
3. whether the key is at least allowed to use `Geocoding API`
4. whether the address is too vague for geocoding to resolve

### Case 3: the browser console says Google Maps failed to load

Check these first:

1. whether `Maps JavaScript API` was actually enabled
2. whether billing is attached to the current project
3. whether the frontend key's API restriction was mistakenly set to another API
4. whether the referrer restriction is missing the current domain or port

## 11. Recommended final configuration for this project

Recommended during development:

- `GOOGLE_MAPS_API_KEY`
  - Application restriction: `HTTP referrers`
  - API restriction: `Maps JavaScript API`
- `GOOGLE_MAPS_GEOCODING_API_KEY`
  - API restriction: `Geocoding API`
  - no IP restriction for local development

Recommended after deployment:

- `GOOGLE_MAPS_API_KEY`
  - allow only the production site domain
  - allow only `Maps JavaScript API`
- `GOOGLE_MAPS_GEOCODING_API_KEY`
  - allow only `Geocoding API`
  - add the server's public IP restriction

## 12. Official references

- Google Maps Platform Getting Started
  <https://developers.google.com/maps/get-started>
- Maps JavaScript API
  <https://developers.google.com/maps/documentation/javascript>
- Geocoding API setup
  <https://developers.google.com/maps/documentation/geocoding/get-api-key>
- Google Maps Platform API security best practices
  <https://developers.google.com/maps/api-security-best-practices>
- Google Cloud API key management and restrictions
  <https://cloud.google.com/docs/authentication/api-keys>
