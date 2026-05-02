"""Google Maps geocoding integration — all graceful-degradation paths."""

from __future__ import annotations

from unittest.mock import Mock, patch

import requests

from criktrack.integrations import geocoding


def _fake(payload):
    resp = Mock(status_code=200)
    resp.json.return_value = payload
    resp.raise_for_status = lambda: None
    return resp


def test_geocode_returns_none_without_key(app):
    app.config["GOOGLE_MAPS_GEOCODING_API_KEY"] = ""
    app.config["GOOGLE_MAPS_API_KEY"] = ""
    with app.app_context():
        assert geocoding.geocode_address("UWA Sports Park") is None


def test_geocode_parses_successful_response(app):
    app.config["GOOGLE_MAPS_GEOCODING_API_KEY"] = "test-key"
    resp = _fake({
        "status": "OK",
        "results": [{"geometry": {"location": {"lat": -31.98, "lng": 115.82}}}],
    })
    with app.app_context(), patch.object(geocoding.requests, "get", return_value=resp):
        assert geocoding.geocode_address("UWA Sports Park") == (-31.98, 115.82)


def test_geocode_returns_none_on_zero_results(app):
    app.config["GOOGLE_MAPS_GEOCODING_API_KEY"] = "test-key"
    resp = _fake({"status": "ZERO_RESULTS", "results": []})
    with app.app_context(), patch.object(geocoding.requests, "get", return_value=resp):
        assert geocoding.geocode_address("nowhere xyz abc") is None


def test_geocode_returns_none_on_network_failure(app):
    app.config["GOOGLE_MAPS_GEOCODING_API_KEY"] = "test-key"
    with app.app_context(), patch.object(
        geocoding.requests, "get", side_effect=requests.Timeout("boom")
    ):
        assert geocoding.geocode_address("UWA") is None


def test_geocode_does_not_fall_back_to_browser_key(app):
    """The browser-exposed Maps JS key must not be reused for server-side calls."""
    app.config["GOOGLE_MAPS_GEOCODING_API_KEY"] = ""
    app.config["GOOGLE_MAPS_API_KEY"] = "maps-key"
    with app.app_context(), patch.object(geocoding.requests, "get") as g:
        assert geocoding.geocode_address("Somewhere") is None
        g.assert_not_called()
