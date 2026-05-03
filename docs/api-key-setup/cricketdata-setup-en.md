# CRIKTRACK CricketData.org Setup Guide

This guide is based on the current code in this project. It is intended for local development and walks through how to configure a CricketData.org API key, understand the code path, and verify that the live cricket feed is working correctly.

Applicable date: 2026-05-01
Project: `CRIKTRACK`
Recommended practice: keep `CRICKETDATA_API_KEY` only in the Flask backend environment. Do not expose it to the browser.

## 1. Understand how CricketData.org is used in this project

In this project, CricketData.org is used only for the **live cricket widget**. The browser does not call the third-party API directly. Instead, it goes through our Flask proxy first:

1. After the page loads, the frontend requests `/api/live/matches` from this project.
2. The Flask backend reads `CRICKETDATA_API_KEY` and calls CricketData.org's `currentMatches` endpoint.
3. The backend returns the upstream result to the frontend and adds cache-related response headers.
4. The frontend polls again after a fixed interval to refresh the live scores.

Relevant code:

- Environment variable example: `app/.env.example`
- Config loading: `app/config.py`
- Frontend config injection: `app/criktrack/__init__.py`
- Backend proxy and cache: `app/criktrack/integrations/cricketdata.py`
- Flask route: `app/criktrack/live/routes.py`
- Frontend polling and rendering: `app/criktrack/static/js/livefeed.js`
- Widget mount points:
  - `app/criktrack/templates/dashboard_user.html`
  - `app/criktrack/templates/tournaments/public.html`

## 2. Register on CricketData.org and get an API key

According to the current official docs, CricketData.org provides free signup and an API key. The pricing page currently shows a free tier of **100 hits/day**. The official docs also note that:

- your API key is available in the member dashboard after signup
- the dashboard includes an API playground / test tool
- playground tests also count toward your API hit quota

Official links:

- Home page: <https://cricketdata.org/>
- Getting started: <https://cricketdata.org/how-to-get-started-with-cricket-data/>
- Pricing: <https://cricketdata.org/pricing/>
- Docs entry: <https://cricketdata.org/how-to-use-cricket-data-api.aspx>

Steps:

1. Open the CricketData.org website and register an account.
2. Log in to the member dashboard.
3. Find your API key.
4. Use the API test / playground in the dashboard to confirm that you can access the `currentMatches` endpoint.

The upstream endpoint used by this project is:

```text
https://api.cricapi.com/v1/currentMatches?apikey=YOUR_API_KEY&offset=0
```

This matches the official examples for live score / current matches.

## 3. Configure the key in this project

This project reads configuration from `app/.env`. The logic already exists in `app/config.py`, so no Python code changes are needed.

### 3.1 Create `.env`

If you do not already have `.env`:

```bash
cd app
cp .env.example .env
```

### 3.2 Edit `app/.env`

At minimum, make sure these values are set:

```env
CRICKETDATA_API_KEY=your_cricketdata_key
LIVE_FEED_CACHE_SECONDS=30
LIVE_FEED_POLL_MS=30000
```

Meaning:

- `CRICKETDATA_API_KEY`
  - Used by the Flask backend to call CricketData.org
  - Do **not** put it into frontend JS
- `LIVE_FEED_CACHE_SECONDS`
  - Backend cache TTL, default `30`
- `LIVE_FEED_POLL_MS`
  - Frontend polling interval, default `30000` milliseconds, which is 30 seconds

Recommendations:

- If you want to conserve API hits during local development, increase `LIVE_FEED_POLL_MS`, for example to `60000`.
- If you refresh often, open multiple tabs, and use the playground, it is easy to exhaust the free quota.

## 4. Understand how these settings take effect in code

You do not need to edit code here, but you should understand the data flow:

1. `app/config.py` reads:
   - `CRICKETDATA_API_KEY`
   - `LIVE_FEED_CACHE_SECONDS`
   - `LIVE_FEED_POLL_MS`
2. `app/criktrack/__init__.py` injects these values into `window.CTM_CONFIG` in templates:
   - `liveFeedEndpoint`
   - `liveFeedPollMs`
3. `app/criktrack/static/js/livefeed.js` looks for:

   ```html
   <div data-ctm-livefeed></div>
   ```

4. Once the mount point is found, the frontend requests:

   ```text
   /api/live/matches
   ```

5. `app/criktrack/live/routes.py` calls `fetch_live_matches()`.
6. `app/criktrack/integrations/cricketdata.py` uses `CRICKETDATA_API_KEY` to call:

   ```text
   https://api.cricapi.com/v1/currentMatches?apikey=...&offset=0
   ```

7. The backend returns one of four states:
   - `live`: freshly fetched from upstream
   - `cache`: returned from in-process cache
   - `stale`: upstream failed, but an older cache entry still exists
   - `mock`: no key, or no usable upstream result is available

## 5. How the proxy cache works

This is the easiest part of the integration to overlook, and the most important one.

`app/criktrack/integrations/cricketdata.py` uses an **in-process TTL cache**:

- Cached content: the last successful payload
- Cache duration: `LIVE_FEED_CACHE_SECONDS`
- Thread safety: reads and writes are protected by a `Lock`

Actual behavior:

1. If `CRICKETDATA_API_KEY` is empty:
   - no upstream request is sent
   - it returns:

   ```json
   {"status": "mock", "data": []}
   ```

2. If the key exists and the cache has not expired:
   - no upstream request is sent
   - the cached payload is returned directly

3. If the key exists and the cache has expired:
   - request upstream `currentMatches`
   - on success: refresh the cache and return the latest payload
   - on failure: if an older cache exists, return the cached payload
   - on failure with no cache: return an empty mock/error-shaped payload

Why this design exists:

- to reduce free-tier quota usage
- to avoid hitting the third-party API on every frontend poll
- to keep the page usable if the upstream service times out or briefly fails

## 6. How to read the response headers

The `/api/live/matches` route uses response headers to tell you which branch was taken:

- `X-CTM-Source: live`
  - this request successfully fetched fresh data from upstream
- `X-CTM-Cache: HIT`
  - this request used the cache directly
- `X-CTM-Stale: 1`
  - upstream failed, but stale cached data was still available
- `X-CTM-Source: mock`
  - no real live data was fetched

These headers are very useful when debugging.

## 7. Start the project

```bash
cd app
source .venv/bin/activate
flask --app run:app db upgrade
flask --app run:app run
```

Default address:

- <http://127.0.0.1:5000/>

If you just changed `.env`, remember to **restart the Flask development server**.

## 8. Start with the local API route as a minimal test

It is better to test the backend proxy first before looking at the page.

### 8.1 Open it in the browser

Open:

- <http://127.0.0.1:5000/api/live/matches>

You should see JSON.

### 8.2 Use `curl` to inspect headers

```bash
curl -i http://127.0.0.1:5000/api/live/matches
```

Focus on:

- whether `X-CTM-Source: live` is present
- whether `X-CTM-Cache: HIT` is present
- whether `X-CTM-Stale: 1` is present
- whether `data` in the response body is an array

You can call it twice:

```bash
curl -i http://127.0.0.1:5000/api/live/matches
curl -i http://127.0.0.1:5000/api/live/matches
```

In the ideal case:

1. the first request shows `X-CTM-Source: live`
2. the second request, if still within the TTL, shows `X-CTM-Cache: HIT`

## 9. Then validate the widget in the UI

In the current repository, the live widget appears on:

1. the user dashboard
2. the tournament public share page

Suggested validation flow:

1. Log in and open the dashboard.
2. Find the `Live cricket` section.
3. Open browser DevTools:
   - `Network` for `/api/live/matches`
   - `Response Headers` for `X-CTM-*`
   - `Response` for the JSON payload
4. If the public share page also shows the widget, open the public page and verify that it loads for anonymous users as well.

Expected results:

1. If the key is valid and upstream is healthy:
   - the widget shows live matches
   - the source label shows `CricketData.org`
2. If the key is not configured:
   - the page still loads
   - the widget shows an empty state
   - the backend `/api/live/matches` returns `{"status":"mock","data":[]}`
3. If upstream briefly fails but an earlier cache entry exists:
   - the widget can still show older data
   - the response includes `X-CTM-Stale: 1`

## 10. Run the existing automated tests

This repository already includes unit tests for the live feed. They mainly cover:

- returning mock when no key is configured
- first request is live, second request is a cache hit
- stale fallback when upstream fails

Relevant file:

- `app/tests/unit/test_live_feed.py`

Run it with:

```bash
cd app
source .venv/bin/activate
.venv/bin/python -m pytest tests/unit/test_live_feed.py -v
```

If you want to run the full suite:

```bash
cd app
source .venv/bin/activate
.venv/bin/python -m pytest tests -q
```

Notes:

- these tests do not call CricketData.org for real
- they use mocks / patches, so they do not consume your API quota

## 11. Quick troubleshooting

### Case 1: the live widget is always empty

Check these first:

1. whether `CRICKETDATA_API_KEY` is set in `app/.env`
2. whether Flask was restarted after `.env` was changed
3. whether `/api/live/matches` is returning `mock`
4. whether there were simply no live matches at that moment, leaving `data` empty

### Case 2: the page opens, but `/api/live/matches` fails in Network

Check these first:

1. whether the Flask server is running correctly
2. whether `window.CTM_CONFIG.liveFeedEndpoint` is injected correctly
3. whether the current page loads `livefeed.js`

### Case 3: `/api/live/matches` always returns `mock`

Check these first:

1. whether `CRICKETDATA_API_KEY` is empty
2. whether Flask read the latest `.env`
3. whether you updated one env file while a different Flask process is actually running

### Case 4: the first load has data, but it does not seem to refresh later

Check these first:

1. whether `LIVE_FEED_POLL_MS` is larger than expected
2. whether `LIVE_FEED_CACHE_SECONDS` is longer than expected
3. whether what you are seeing is simply a cache hit: `X-CTM-Cache: HIT`

### Case 5: upstream fails occasionally, but the page does not fully break

This is usually not a bug. It means the stale-cache fallback is working. Check the headers:

- if `X-CTM-Stale: 1` is present
  - upstream failed for this request
  - but older cached data was still available
  - this is expected behavior in the current design

## 12. Current implementation boundaries

There are a few details you should know:

1. This key is **backend-only**.
   - the browser never receives `CRICKETDATA_API_KEY`
2. The current cache is a **single-process in-memory cache**.
   - fine for local development
   - if the app later runs with multiple workers, they will not share cache state
3. The current proxy only distinguishes between "HTTP request success/failure" and "cache available/unavailable".
   - it does not perform complex business validation on the CricketData payload
   - if upstream returns a semantically bad JSON payload with HTTP `200`, the current code will still cache it as a successful payload
4. The current widget renders a simplified list:
   - it mainly reads `data`
   - for each match it mostly uses `teamInfo`, `score`, and `status`

## 13. Recommended development configuration

Recommended for local development:

```env
CRICKETDATA_API_KEY=your_key
LIVE_FEED_CACHE_SECONDS=30
LIVE_FEED_POLL_MS=30000
```

If you want to conserve quota, temporarily use:

```env
LIVE_FEED_CACHE_SECONDS=60
LIVE_FEED_POLL_MS=60000
```

This makes the frontend poll once per minute and keeps the backend cache for one minute, which is better for demos or UI debugging.

## 14. Official references

- CricketData.org home page
  <https://cricketdata.org/>
- Getting started
  <https://cricketdata.org/how-to-get-started-with-cricket-data/>
- Pricing
  <https://cricketdata.org/pricing/>
- API docs / how to use
  <https://cricketdata.org/how-to-use-cricket-data-api.aspx>
- Live score quickstart
  <https://cricketdata.org/live-cricket-score-api/>
