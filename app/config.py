import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _required(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-do-not-use-in-prod")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///criktrack.sqlite3"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = 3600

    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    GOOGLE_MAPS_GEOCODING_API_KEY = os.environ.get("GOOGLE_MAPS_GEOCODING_API_KEY", "")
    CRICKETDATA_API_KEY = os.environ.get("CRICKETDATA_API_KEY", "")

    LIVE_FEED_CACHE_SECONDS = int(os.environ.get("LIVE_FEED_CACHE_SECONDS", 30))
    LIVE_FEED_POLL_MS = int(os.environ.get("LIVE_FEED_POLL_MS", 30000))

    ORGANIZER_INVITE_CODE = os.environ.get("ORGANIZER_INVITE_CODE", "")


class DevConfig(BaseConfig):
    DEBUG = True


class TestConfig(BaseConfig):
    TESTING = True
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
