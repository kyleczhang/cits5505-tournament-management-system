from __future__ import annotations

from flask import jsonify

from ..integrations.cricketdata import fetch_live_matches
from . import bp


@bp.route("/matches")
def matches():
    payload, status = fetch_live_matches()
    return jsonify({"status": status, "data": payload.get("data", [])})
