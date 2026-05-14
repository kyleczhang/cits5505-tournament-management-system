"""Venue model — physical match locations with optional geocoded coordinates."""

from __future__ import annotations

from ..extensions import db


class Venue(db.Model):
    """A ground or stadium; lat/lng are populated by integrations.geocoding when available."""

    __tablename__ = "venues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)

    @property
    def has_coords(self) -> bool:
        """Return whether both venue coordinates are available."""
        return self.lat is not None and self.lng is not None

    def to_dict(self) -> dict:
        """Serialise for client-side map rendering (see static/js/maps.js)."""
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "lat": self.lat,
            "lng": self.lng,
        }
