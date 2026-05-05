"""Routes for the live cricket feed proxy.

Wraps :func:`fetch_live_matches` and surfaces the cache/source state to
clients via custom response headers so the front-end can show whether
data is fresh, cached, stale, or mocked.
"""

from flask import jsonify

from ..integrations.cricketdata import fetch_live_matches
from . import bp


@bp.route("/matches", methods=["GET"])
def matches():
    payload, status = fetch_live_matches()
    response = jsonify(payload)
    # Map the integration's status into observable headers:
    #   cache -> served from in-process TTL cache (X-CTM-Cache: HIT)
    #   stale -> upstream failed, returning last known payload
    #   mock  -> no API key configured; returning canned demo data
    #   live  -> fresh fetch from cricketdata.org
    if status == "cache":
        response.headers["X-CTM-Cache"] = "HIT"
    elif status == "stale":
        response.headers["X-CTM-Stale"] = "1"
    elif status == "mock":
        response.headers["X-CTM-Source"] = "mock"
    else:
        response.headers["X-CTM-Source"] = "live"
    return response
