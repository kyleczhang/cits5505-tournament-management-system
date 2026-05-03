"""Selenium smoke tests — end-to-end user flows.

Requires Chrome + a matching chromedriver on PATH. Tests skip automatically
if the driver is unavailable.
"""

from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.selenium

selenium = pytest.importorskip("selenium")
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402


def _wait(browser, timeout: float = 4.0):
    return WebDriverWait(browser, timeout)


def _unique_email() -> str:
    return f"sel-{uuid.uuid4().hex[:8]}@example.com"


def _submit_form(browser, button_name: str = "submit") -> None:
    btn = browser.find_element(By.NAME, button_name)
    browser.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    browser.execute_script("arguments[0].click();", btn)


def _register(
    browser,
    base_url: str,
    email: str,
    display_name: str = "Selena Test",
    password: str = "secret123",
) -> None:
    browser.get(f"{base_url}/register")
    browser.find_element(By.NAME, "display_name").send_keys(display_name)
    browser.find_element(By.NAME, "email").send_keys(email)
    browser.find_element(By.NAME, "password").send_keys(password)
    browser.find_element(By.NAME, "password_confirm").send_keys(password)
    browser.execute_script("document.getElementsByName('terms')[0].checked = true;")
    _submit_form(browser)
    _wait(browser).until(EC.url_contains("/dashboard"))


def test_landing_page_loads(browser, live_server):
    browser.get(live_server["url"] + "/")
    assert "CRIKTRACK" in browser.title


def test_user_can_register_and_reach_dashboard(browser, live_server):
    email = _unique_email()
    _register(browser, live_server["url"], email)
    assert "/dashboard" in browser.current_url


def test_user_can_log_out_and_log_back_in(browser, live_server):
    email = _unique_email()
    _register(browser, live_server["url"], email)

    # Log out via the POST form in the nav.
    logout = browser.find_element(
        By.CSS_SELECTOR, "form[action*='/logout'] button[type='submit']"
    )
    browser.execute_script("arguments[0].click();", logout)
    _wait(browser).until(lambda b: "/dashboard" not in b.current_url)

    browser.get(live_server["url"] + "/login")
    browser.find_element(By.NAME, "email").send_keys(email)
    browser.find_element(By.NAME, "password").send_keys("secret123")
    _submit_form(browser)
    _wait(browser).until(EC.url_contains("/dashboard"))


def test_anonymous_dashboard_redirects_to_login(browser, live_server):
    browser.get(live_server["url"] + "/dashboard")
    _wait(browser).until(EC.url_contains("/login"))
    assert "/login" in browser.current_url


def test_tournaments_list_page_loads(browser, live_server):
    browser.get(live_server["url"] + "/tournaments")
    _wait(browser).until(EC.presence_of_element_located((By.TAG_NAME, "main")))
    body = browser.find_element(By.TAG_NAME, "body").text.lower()
    assert "tournament" in body


def test_register_form_rejects_weak_password(browser, live_server):
    browser.get(live_server["url"] + "/register")
    browser.find_element(By.NAME, "display_name").send_keys("Weak Pw")
    browser.find_element(By.NAME, "email").send_keys(_unique_email())
    browser.find_element(By.NAME, "password").send_keys("short")
    browser.find_element(By.NAME, "password_confirm").send_keys("short")
    browser.execute_script("document.getElementsByName('terms')[0].checked = true;")
    _submit_form(browser)
    # Stays on register because server-side validation rejects.
    assert "/register" in browser.current_url
