"""Live cricket match feed module.

This blueprint provides real-time live cricket match data, supporting source
awareness through HTTP response headers. It proxies CricketData.org via the
integrations.cricketdata module, which implements TTL-based caching with a
mock fallback for offline operation.

Data Flow:
  1. Client requests /api/live/matches (polled every 30s by livefeed.js)
  2. Flask route calls cricketdata.fetch_live_matches()
  3. cricketdata returns (payload, status) tuple
  4. Route sets response headers based on status (live, cache, stale, mock)
  5. Client-side livefeed.js reads headers and renders data with source labels

Response Headers:
  - X-CTM-Source: "live" (fresh data) or "mock" (fallback)
  - X-CTM-Cache: "HIT" (cached within TTL)
  - X-CTM-Stale: "1" (cache expired, using stale data)

Frontend Integration:
  - livefeed.js parses these headers via response.headers.get()
  - Renders source label: "Live" | "Cached" | "Stale" | "Mock"
  - Falls back to mockdata if endpoint unavailable
"""

from flask import jsonify

from . import bp
from ..integrations.cricketdata import fetch_live_matches


@bp.route("/matches", methods=["GET"])
def matches():
    """Fetch live cricket matches with source awareness.

    Returns:
        JSON response with live match data. Response headers indicate
        whether data is live, cached, stale, or from mock fallback.
    """
    payload, status = fetch_live_matches()
    response = jsonify(payload)
    if status == "cache":
        response.headers["X-CTM-Cache"] = "HIT"
    elif status == "stale":
        response.headers["X-CTM-Stale"] = "1"
    elif status == "mock":
        response.headers["X-CTM-Source"] = "mock"
    else:
        response.headers["X-CTM-Source"] = "live"
    return response