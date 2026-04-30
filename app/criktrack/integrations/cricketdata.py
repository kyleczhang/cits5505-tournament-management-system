"""CricketData.org proxy with in-process TTL cache."""

from __future__ import annotations

import time
from threading import Lock
from typing import Any

import requests
from flask import current_app

_API_URL = "https://api.cricapi.com/v1/currentMatches"

_cache_lock = Lock()
_cache: dict[str, Any] = {"payload": None, "fetched_at": 0.0}


def _ttl() -> int:
    return int(current_app.config.get("LIVE_FEED_CACHE_SECONDS", 30))


def fetch_live_matches() -> tuple[dict, str]:
    """Return (payload, status) where status is 'live'|'cache'|'stale'|'mock'.

    'live'  — fresh upstream response
    'cache' — cached upstream response, still inside TTL
    'stale' — upstream failed but we have a previous payload
    'mock'  — no key configured / no payload available
    """
    api_key = current_app.config.get("CRICKETDATA_API_KEY", "")
    now = time.time()

    with _cache_lock:
        cached = _cache["payload"]
        fetched = _cache["fetched_at"]

    if not api_key:
        return ({"status": "mock", "data": []}, "mock")

    if cached is not None and (now - fetched) < _ttl():
        return (cached, "cache")

    try:
        resp = requests.get(
            _API_URL,
            params={"apikey": api_key, "offset": 0},
            timeout=4,
        )
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError):
        if cached is not None:
            return (cached, "stale")
        return ({"status": "error", "data": []}, "mock")

    with _cache_lock:
        _cache["payload"] = payload
        _cache["fetched_at"] = now
    return (payload, "live")


def reset_cache() -> None:
    """For tests — clear the in-process cache."""
    with _cache_lock:
        _cache["payload"] = None
        _cache["fetched_at"] = 0.0
