from flask import jsonify

from ..integrations.cricketdata import fetch_live_matches
from . import bp


@bp.route("/matches", methods=["GET"])
def matches():
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
