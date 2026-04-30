"""Server-side geocoding via Google Maps Geocoding API."""

from __future__ import annotations

import requests
from flask import current_app

_API_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def geocode_address(address: str) -> tuple[float, float] | None:
    """Return (lat, lng) for the address, or None if geocoding is unavailable.

    Returns None when:
      - no API key is configured (dev/test default)
      - the upstream call fails or times out
      - Google returns ZERO_RESULTS / OVER_QUERY_LIMIT / INVALID_REQUEST
    """
    address = (address or "").strip()
    if not address:
        return None

    api_key = current_app.config.get("GOOGLE_MAPS_GEOCODING_API_KEY", "")
    if not api_key:
        return None

    try:
        resp = requests.get(
            _API_URL,
            params={"address": address, "key": api_key},
            timeout=4,
        )
        resp.raise_for_status()
        body = resp.json()
    except (requests.RequestException, ValueError):
        return None

    if body.get("status") != "OK":
        return None
    results = body.get("results") or []
    if not results:
        return None
    loc = results[0].get("geometry", {}).get("location") or {}
    lat = loc.get("lat")
    lng = loc.get("lng")
    if lat is None or lng is None:
        return None
    return float(lat), float(lng)
