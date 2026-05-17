"""End-to-end Selenium coverage of the organiser workflow.

These tests complement ``test_smoke.py`` by driving the real organiser
journey through the browser against the live Flask server:

* register with the organiser invite code
* create teams + a tournament
* schedule a fixture
* anonymous public share view
* record a match result by filling and submitting the in-page record form
* post a comment through the real <textarea> + submit button, asserting
  that the rendered comment DOM updates as ``comments.js`` expects
* follow / unfollow a tournament by clicking the rendered follow button
  and asserting the button's text + ``data-following`` + ``aria-pressed``
  flip in response

Every interactive flow is driven through the browser DOM — no direct
fetch() calls, so a broken event binding in the JS will fail the test.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest

pytestmark = pytest.mark.selenium

selenium = pytest.importorskip("selenium")
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import Select, WebDriverWait  # noqa: E402

# --- shared helpers ---------------------------------------------------------


def _wait(browser, timeout: float = 5.0):
    return WebDriverWait(browser, timeout)


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _submit_form(browser, button_name: str = "submit") -> None:
    btn = browser.find_element(By.NAME, button_name)
    browser.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    browser.execute_script("arguments[0].click();", btn)


def _register_organiser(browser, base_url: str) -> tuple[str, str]:
    """Register a fresh organiser account; returns (email, display_name)."""
    email = f"{_unique('org')}@example.com"
    display = "Org " + uuid.uuid4().hex[:4]
    browser.get(f"{base_url}/register")
    browser.find_element(By.NAME, "display_name").send_keys(display)
    browser.find_element(By.NAME, "email").send_keys(email)
    browser.find_element(By.NAME, "password").send_keys("secret123")
    browser.find_element(By.NAME, "password_confirm").send_keys("secret123")
    browser.find_element(By.NAME, "invite_code").send_keys("test-invite")
    browser.execute_script("document.getElementsByName('terms')[0].checked = true;")
    _submit_form(browser)
    _wait(browser).until(EC.url_contains("/dashboard"))
    return email, display


def _create_team(browser, base_url: str, name: str, short_code: str) -> int:
    """Create a team via the /teams/create form and return its DB id."""
    browser.get(f"{base_url}/teams/create")
    browser.find_element(By.NAME, "name").send_keys(name)
    browser.find_element(By.NAME, "short_code").send_keys(short_code)
    _submit_form(browser)
    _wait(browser).until(EC.url_matches(r"/teams/\d+"))
    # /teams/<id> — pull id from the URL.
    return int(browser.current_url.rstrip("/").split("/")[-1])


def _create_tournament(browser, base_url: str, name: str, team_ids: list[int]) -> int:
    """Create a tournament that registers `team_ids`. Returns tournament id."""
    browser.get(f"{base_url}/tournaments/create")
    browser.find_element(By.NAME, "name").send_keys(name)
    Select(browser.find_element(By.NAME, "format")).select_by_value("round_robin")
    # The date input expects YYYY-MM-DD — write it directly to bypass locale issues.
    future = (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d")
    browser.execute_script(
        "arguments[0].value = arguments[1];",
        browser.find_element(By.NAME, "start_date"),
        future,
    )
    # The <select multiple> is visually-hidden behind a custom picker; the form
    # still submits the underlying <option>s so toggling them in JS is enough.
    select_el = browser.find_element(By.NAME, "team_ids")
    select = Select(select_el)
    for tid in team_ids:
        select.select_by_value(str(tid))
    _submit_form(browser)
    _wait(browser, 8).until(EC.url_matches(r"/tournaments/\d+$"))
    return int(browser.current_url.rstrip("/").split("/")[-1])


def _schedule_match(
    browser, base_url: str, tournament_id: int, team_a_id: int, team_b_id: int
) -> None:
    """Schedule one fixture between two registered teams."""
    browser.get(f"{base_url}/tournaments/{tournament_id}/matches/create")
    Select(browser.find_element(By.NAME, "team_a_id")).select_by_value(str(team_a_id))
    Select(browser.find_element(By.NAME, "team_b_id")).select_by_value(str(team_b_id))
    when = (datetime.utcnow() + timedelta(days=21)).strftime("%Y-%m-%dT%H:%M")
    browser.execute_script(
        "arguments[0].value = arguments[1];",
        browser.find_element(By.NAME, "scheduled_at"),
        when,
    )
    _submit_form(browser)
    _wait(browser, 8).until(EC.url_matches(rf"/tournaments/{tournament_id}$"))


def _click(browser, element) -> None:
    """Scroll an element into view and JS-click it (defeats sticky-header overlap)."""
    browser.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    browser.execute_script("arguments[0].click();", element)


# --- tests ------------------------------------------------------------------


def test_organiser_creates_teams_tournament_and_fixture(browser, live_server):
    """Organiser end-to-end: register → create teams → tournament → schedule match."""
    base = live_server["url"]
    _register_organiser(browser, base)

    team_a_name = _unique("Alpha")
    team_b_name = _unique("Bravo")
    team_a_id = _create_team(browser, base, team_a_name, "ALP")
    team_b_id = _create_team(browser, base, team_b_name, "BRV")

    tournament_name = _unique("Cup")
    tournament_id = _create_tournament(
        browser, base, tournament_name, [team_a_id, team_b_id]
    )

    # Detail page should list both registered teams and the organiser tools.
    page = browser.find_element(By.TAG_NAME, "body").text
    assert team_a_name in page
    assert team_b_name in page
    assert "Schedule match" in page

    _schedule_match(browser, base, tournament_id, team_a_id, team_b_id)

    # Back on the detail page — fixture should now appear in the Fixtures tab.
    body = browser.find_element(By.TAG_NAME, "body").text
    assert team_a_name in body and team_b_name in body
    assert "Upcoming" in body or "upcoming" in body.lower()


def test_organiser_can_add_third_team_after_creation(browser, live_server):
    """The 'Add team' form on the detail page registers an extra team mid-flight."""
    base = live_server["url"]
    _register_organiser(browser, base)

    a = _create_team(browser, base, _unique("Alpha"), "ALP")
    b = _create_team(browser, base, _unique("Bravo"), "BRV")
    spare_name = _unique("Sharks")
    spare = _create_team(browser, base, spare_name, "SHK")

    tid = _create_tournament(browser, base, _unique("Cup"), [a, b])

    # Now add the spare team via the inline organiser form.
    browser.get(f"{base}/tournaments/{tid}")
    add_select = browser.find_element(By.CSS_SELECTOR, "select[name=team_id]")
    Select(add_select).select_by_value(str(spare))
    form = add_select.find_element(By.XPATH, "ancestor::form")
    # Capture an element from the current page so we can wait for the post-submit
    # navigation to actually replace the DOM (the URL doesn't change here, so
    # EC.url_matches isn't a useful gate).
    old_body = browser.find_element(By.TAG_NAME, "body")
    form.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
    _wait(browser).until(EC.staleness_of(old_body))
    assert spare_name in browser.find_element(By.TAG_NAME, "body").text


def test_anonymous_visitor_can_view_public_share_page(browser, live_server):
    """The /<slug>/share view is reachable without login and shows the tournament."""
    base = live_server["url"]
    _register_organiser(browser, base)
    a = _create_team(browser, base, _unique("Alpha"), "ALP")
    b = _create_team(browser, base, _unique("Bravo"), "BRV")
    name = _unique("PublicCup")
    tid = _create_tournament(browser, base, name, [a, b])

    # Grab the share URL from the detail page's share button.
    browser.get(f"{base}/tournaments/{tid}")
    share_url = browser.find_element(
        By.CSS_SELECTOR, "button[data-share]"
    ).get_attribute("data-share")
    assert "/share" in share_url

    # Log out by clearing cookies and visit the share URL as anonymous.
    browser.delete_all_cookies()
    browser.get(share_url)
    body = browser.find_element(By.TAG_NAME, "body").text
    assert name in body
    # Anonymous nav shouldn't try to bounce us to /login.
    assert "/login" not in browser.current_url


def test_organiser_records_match_result_from_the_record_form(browser, live_server):
    """Fill toss/winner/result fields in /record and click Save — verifies record.js
    submit handler, CSRF wiring, redirect target, and scorecard render after save.
    """
    base = live_server["url"]
    _register_organiser(browser, base)
    a_name = _unique("Alpha")
    b_name = _unique("Bravo")
    a = _create_team(browser, base, a_name, "ALP")
    b = _create_team(browser, base, b_name, "BRV")
    tid = _create_tournament(browser, base, _unique("Cup"), [a, b])
    _schedule_match(browser, base, tid, a, b)

    # Discover the new match id from the "Enter result" link rendered for organisers.
    browser.get(f"{base}/tournaments/{tid}")
    link = browser.find_element(
        By.CSS_SELECTOR, f"a[href*='/tournaments/{tid}/matches/'][href$='/record']"
    )
    record_href = link.get_attribute("href")
    match_id = int(record_href.rstrip("/").split("/")[-2])
    scorecard_url = f"{base}/tournaments/{tid}/matches/{match_id}"

    # Drive the actual record form: toss selects, winner select, result_text input,
    # then click the real submit button. record.js handles the rest.
    browser.get(record_href)
    _wait(browser).until(EC.presence_of_element_located((By.ID, "record-form")))
    Select(browser.find_element(By.ID, "toss_winner")).select_by_value(str(a))
    Select(browser.find_element(By.ID, "toss_decision")).select_by_value("bat")
    # Winner select + result_text input live in a Bootstrap tab that isn't the
    # default pane — set their values via JS so we don't depend on a tab click.
    result_text = "Alpha won by 12 runs (selenium-" + uuid.uuid4().hex[:6] + ")"
    browser.execute_script(
        "document.getElementById('winner').value = arguments[0];"
        "document.getElementById('result_text').value = arguments[1];",
        str(a),
        result_text,
    )

    submit_btn = browser.find_element(
        By.CSS_SELECTOR, "#record-form button[type='submit']"
    )
    _click(browser, submit_btn)

    # record.js sets location.href = data.redirect on success → wait for scorecard.
    _wait(browser, 8).until(EC.url_to_be(scorecard_url))

    body = browser.find_element(By.TAG_NAME, "body").text
    # Completed badge + winner's name + result text must render after save.
    # The badge text is uppercased via CSS, so compare case-insensitively.
    assert "completed" in body.lower(), body
    assert a_name in body
    # The dedicated <strong class="match-result-text"> element holds the result text.
    result_el = browser.find_element(By.CSS_SELECTOR, ".match-result-text")
    assert result_text in result_el.text


def test_record_form_shows_inline_errors_on_invalid_payload(browser, live_server):
    """Submitting record with toss=A/bat but winner from team B yields no validation
    failure (winner is one of two teams), but mismatched toss/innings *does* — we
    use a different invalid combo: toss winner not in {team_a, team_b} via DOM tampering.
    A simpler observable failure: blank toss with a winner is allowed; instead we
    force an error by writing a bogus winner value, confirming the error box shows.
    """
    base = live_server["url"]
    _register_organiser(browser, base)
    a = _create_team(browser, base, _unique("Alpha"), "ALP")
    b = _create_team(browser, base, _unique("Bravo"), "BRV")
    tid = _create_tournament(browser, base, _unique("Cup"), [a, b])
    _schedule_match(browser, base, tid, a, b)

    browser.get(f"{base}/tournaments/{tid}")
    record_href = browser.find_element(
        By.CSS_SELECTOR, f"a[href*='/tournaments/{tid}/matches/'][href$='/record']"
    ).get_attribute("href")

    browser.get(record_href)
    _wait(browser).until(EC.presence_of_element_located((By.ID, "record-form")))

    # Inject a winner option that isn't one of the two real teams; the server's
    # validator rejects it and record.js renders the response into #record-errors.
    browser.execute_script(
        "var s = document.getElementById('winner');"
        "var o = document.createElement('option');"
        "o.value = '99999'; o.textContent = 'Bogus'; o.selected = true;"
        "s.appendChild(o);"
    )

    submit_btn = browser.find_element(
        By.CSS_SELECTOR, "#record-form button[type='submit']"
    )
    _click(browser, submit_btn)

    # .text returns "" for elements that may be off-screen / clipped — read the
    # rendered HTML directly so we test what record.js actually wrote.
    def _err_html(b):
        el = b.find_element(By.ID, "record-errors")
        if "is-hidden" in (el.get_attribute("class") or ""):
            return False
        return el.get_attribute("innerHTML") or False

    html = _wait(browser, 6).until(_err_html).lower()
    assert "winner" in html or "must" in html, html


def test_user_posts_a_comment_through_the_form_and_sees_it_render(browser, live_server):
    """Type into the real <textarea>, click Post comment, and assert the new <li>
    appears in the comment list with the right body text and the count badge updates.
    """
    base = live_server["url"]
    _register_organiser(browser, base)
    a = _create_team(browser, base, _unique("Alpha"), "ALP")
    b = _create_team(browser, base, _unique("Bravo"), "BRV")
    tid = _create_tournament(browser, base, _unique("CommentCup"), [a, b])

    browser.get(f"{base}/tournaments/{tid}")
    section = _wait(browser).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-ctm-comments]"))
    )
    # Wait for comments.js to finish the initial GET and render the empty state.
    _wait(browser).until(
        lambda b: section.find_elements(By.CSS_SELECTOR, "[data-ctm-comment-list] li")
    )

    body_text = "ui-comment-" + uuid.uuid4().hex[:6]
    textarea = section.find_element(By.CSS_SELECTOR, "[data-ctm-comment-form] textarea")
    textarea.clear()
    textarea.send_keys(body_text)
    # The counter must update on input (comments.js binds 'input').
    counter = section.find_element(By.CSS_SELECTOR, "[data-ctm-comment-counter]")
    assert counter.text.startswith(str(len(body_text))), counter.text

    submit = section.find_element(
        By.CSS_SELECTOR, "[data-ctm-comment-form] button[type='submit']"
    )
    _click(browser, submit)

    # The new comment should appear in the rendered list, not just in the DB.
    def _has_comment(b):
        items = section.find_elements(
            By.CSS_SELECTOR, "[data-ctm-comment-list] .ctm-comment-text"
        )
        return any(body_text == el.text for el in items)

    _wait(browser, 6).until(_has_comment)

    # Count badge must reflect 1 comment, and textarea must have been cleared.
    count_el = section.find_element(By.CSS_SELECTOR, "[data-ctm-comment-count]")
    assert "1" in count_el.text, count_el.text
    assert textarea.get_attribute("value") == ""


def test_user_clicks_follow_button_and_state_toggles_in_dom(browser, live_server):
    """Click the rendered follow button: data-following, aria-pressed and label all
    flip on follow, then flip back on a second click. Exercises follow.js end-to-end.
    """
    base = live_server["url"]
    _register_organiser(browser, base)
    a = _create_team(browser, base, _unique("Alpha"), "ALP")
    b = _create_team(browser, base, _unique("Bravo"), "BRV")
    tid = _create_tournament(browser, base, _unique("FollowCup"), [a, b])

    browser.get(f"{base}/tournaments/{tid}")
    btn = _wait(browser).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                f"[data-ctm-follow][data-target-type='tournament']"
                f"[data-target-id='{tid}']",
            )
        )
    )
    assert btn.get_attribute("data-following") == "0"
    assert btn.get_attribute("aria-pressed") == "false"
    label = btn.find_element(By.CSS_SELECTOR, "[data-ctm-follow-label]")
    assert label.text.strip().lower() == "follow"

    _click(browser, btn)
    _wait(browser, 6).until(lambda _: btn.get_attribute("data-following") == "1")
    assert btn.get_attribute("aria-pressed") == "true"
    assert "is-following" in (btn.get_attribute("class") or "")
    assert label.text.strip().lower() == "following"

    # Click again — should unfollow and revert all three attributes.
    _click(browser, btn)
    _wait(browser, 6).until(lambda _: btn.get_attribute("data-following") == "0")
    assert btn.get_attribute("aria-pressed") == "false"
    assert "is-following" not in (btn.get_attribute("class") or "")
    assert label.text.strip().lower() == "follow"


def test_non_organiser_cannot_reach_team_creation(browser, live_server):
    """USER-role accounts are 403'd by @require_role('organizer')."""
    base = live_server["url"]
    email = f"{_unique('user')}@example.com"
    browser.get(f"{base}/register")
    browser.find_element(By.NAME, "display_name").send_keys("Regular Joe")
    browser.find_element(By.NAME, "email").send_keys(email)
    browser.find_element(By.NAME, "password").send_keys("secret123")
    browser.find_element(By.NAME, "password_confirm").send_keys("secret123")
    # Intentionally NO invite code — should default to Role.USER.
    browser.execute_script("document.getElementsByName('terms')[0].checked = true;")
    _submit_form(browser)
    _wait(browser).until(EC.url_contains("/dashboard"))

    browser.get(f"{base}/teams/create")
    # Whether the app shows a 403 page or redirects with a flash, the team form
    # must not be reachable for a non-organiser.
    body = browser.find_element(By.TAG_NAME, "body").text.lower()
    assert "short code" not in body or "forbidden" in body or "403" in body
