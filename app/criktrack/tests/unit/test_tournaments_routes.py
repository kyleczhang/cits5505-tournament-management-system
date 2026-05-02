import pytest

from app.criktrack.tournaments import bp as tournaments_bp


def test_list_view_route_exists(client):
    resp = client.get('/tournaments')
    assert resp.status_code in (200, 302)  # allow redirect to login for protected actions
