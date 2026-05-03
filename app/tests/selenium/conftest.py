"""Selenium fixtures — spin up the Flask app in a background thread."""

from __future__ import annotations

import socket
import threading
import time

import pytest

from config import TestConfig
from criktrack import create_app
from criktrack.extensions import db as _db


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for(host: str, port: int, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"Server on {host}:{port} did not start within {timeout}s")


class _FileTestConfig(TestConfig):
    """Selenium needs a shared DB across threads; in-memory SQLite can't do that."""

    pass


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("db") / "selenium.sqlite3"

    class _Cfg(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"

    app = create_app(_Cfg)
    with app.app_context():
        _db.create_all()

    port = _free_port()
    thread = threading.Thread(
        target=app.run,
        kwargs={
            "host": "127.0.0.1",
            "port": port,
            "use_reloader": False,
            "threaded": True,
        },
        daemon=True,
    )
    thread.start()
    _wait_for("127.0.0.1", port)

    yield {"url": f"http://127.0.0.1:{port}", "app": app}


@pytest.fixture(scope="session")
def browser():
    selenium = pytest.importorskip("selenium")
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,900")

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as exc:
        pytest.skip(f"Chrome webdriver unavailable: {exc}")
    yield driver
    driver.quit()


@pytest.fixture(autouse=True)
def _isolate_session(browser, live_server):
    """Clear cookies before every test so no two tests share a login."""
    browser.get(live_server["url"] + "/")
    browser.delete_all_cookies()
    yield
