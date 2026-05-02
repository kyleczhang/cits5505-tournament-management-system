"""Live cricket proxy — mock/cache/stale/live paths."""

from __future__ import annotations

from unittest.mock import Mock, patch

import requests

from criktrack.integrations import cricketdata


def _fake_response(payload):
    resp = Mock(status_code=200)
    resp.json.return_value = payload
    resp.raise_for_status = lambda: None
    return resp


def test_mock_response_when_no_api_key(client, app):
    app.config["CRICKETDATA_API_KEY"] = ""
    resp = client.get("/api/live/matches")
    assert resp.status_code == 200
    assert resp.headers.get("X-CTM-Source") == "mock"
    assert resp.get_json() == {"status": "mock", "data": []}


def test_live_then_cache_hit(client, app):
    app.config["CRICKETDATA_API_KEY"] = "fake-key"
    app.config["LIVE_FEED_CACHE_SECONDS"] = 30
    fake = _fake_response({"status": "success", "data": [{"id": "1"}]})
    with patch.object(cricketdata.requests, "get", return_value=fake) as g:
        first = client.get("/api/live/matches")
        second = client.get("/api/live/matches")
        assert first.status_code == 200
        assert first.headers.get("X-CTM-Source") == "live"
        assert second.headers.get("X-CTM-Cache") == "HIT"
        assert g.call_count == 1  # cache prevented a second upstream fetch


def test_stale_fallback_on_upstream_failure(client, app):
    app.config["CRICKETDATA_API_KEY"] = "fake-key"
    app.config["LIVE_FEED_CACHE_SECONDS"] = 30
    fake = _fake_response({"status": "success", "data": [{"id": "1"}]})
    with patch.object(cricketdata.requests, "get", return_value=fake):
        client.get("/api/live/matches")
    cricketdata._cache["fetched_at"] = 0.0  # force expiry
    with patch.object(
        cricketdata.requests, "get", side_effect=requests.Timeout("boom")
    ):
        resp = client.get("/api/live/matches")
    assert resp.status_code == 200
    assert resp.headers.get("X-CTM-Stale") == "1"
    assert resp.get_json()["data"] == [{"id": "1"}]
