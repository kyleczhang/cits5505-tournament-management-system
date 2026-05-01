import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class BaseConfig:
    # Signs session cookies and CSRF tokens. No fallback on purpose:
    # create_app() validates this is set so a missing env var fails fast.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    # SQLAlchemy connection string; defaults to a local SQLite file for dev.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///criktrack.sqlite3"
    )
    # Disables SQLAlchemy's per-object change tracking to save memory.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Blocks JS from reading the session cookie (mitigates XSS session theft).
    SESSION_COOKIE_HTTPONLY = True
    # Lax SameSite: cookie sent on top-level navigations but not cross-site POSTs.
    SESSION_COOKIE_SAMESITE = "Lax"
    # CSRF token validity window in seconds (1 hour).
    WTF_CSRF_TIME_LIMIT = 3600

    # Client-side Maps JS API key, exposed to the browser via window.CTM_CONFIG.
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    # Server-side Geocoding API key used by integrations/geocoding.py.
    GOOGLE_MAPS_GEOCODING_API_KEY = os.environ.get("GOOGLE_MAPS_GEOCODING_API_KEY", "")
    # Auth key for cricapi.com live-match feed (integrations/cricketdata.py).
    CRICKETDATA_API_KEY = os.environ.get("CRICKETDATA_API_KEY", "")

    # TTL for the in-process live-feed cache before re-hitting the upstream API.
    LIVE_FEED_CACHE_SECONDS = int(os.environ.get("LIVE_FEED_CACHE_SECONDS", 30))
    # Frontend polling interval (ms) for the live-feed widget.
    LIVE_FEED_POLL_MS = int(os.environ.get("LIVE_FEED_POLL_MS", 30000))

    # Shared secret required at registration to claim the "organizer" role.
    ORGANIZER_INVITE_CODE = os.environ.get("ORGANIZER_INVITE_CODE", "")


class DevConfig(BaseConfig):
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True
    # Use an in-memory SQLite database for tests.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret"
    ORGANIZER_INVITE_CODE = "test-invite"


class ProdConfig(BaseConfig):
    SESSION_COOKIE_SECURE = True

    def __init__(self) -> None:
        if BaseConfig.SECRET_KEY == "dev-only-do-not-use-in-prod":
            raise RuntimeError("SECRET_KEY must be set in production")


def get_config() -> type[BaseConfig]:
    env = os.environ.get("FLASK_ENV", "development").lower()
    if env == "production":
        return ProdConfig
    if env == "testing":
        return TestConfig
    return DevConfig
