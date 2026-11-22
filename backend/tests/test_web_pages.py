import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import ADMIN_PASSWORD, ADMIN_USERNAME


@pytest.fixture
def browser() -> TestClient:
    """A separate client so session cookies don't leak into other tests."""
    return TestClient(app, follow_redirects=False)


@pytest.mark.parametrize("path", ["/dashboard", "/tasks", "/agenda", "/profile", "/admin"])
def test_pages_redirect_to_login_when_logged_out(browser, path):
    response = browser.get(path)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_login_page_renders(browser):
    response = browser.get("/login")
    assert response.status_code == 200
    assert "<form" in response.text


def test_wrong_password_shows_dutch_error(browser):
    response = browser.post("/login", data={"username": ADMIN_USERNAME, "password": "fout"})
    assert response.status_code == 401
    assert "Onjuiste gegevens" in response.text


def test_admin_login_and_logout(browser):
    response = browser.post("/login", data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    assert "buddyplan_session" in browser.cookies

    for path in ["/dashboard", "/admin", "/admin/upgrades", "/admin/ai"]:
        assert browser.get(path).status_code == 200, path
    ai_page = browser.get("/admin/ai").text
    assert "worden naar Google gestuurd" in ai_page  # REQ-BE-081
    assert 'href="/admin/ai" class="active"' in ai_page  # REQ-BE-072

    browser.get("/logout")
    assert browser.get("/dashboard").status_code == 303


ADMIN_SECTIONS = ["/admin", "/admin/afvalwijzer", "/admin/google-calendar-api", "/admin/ai", "/admin/upgrades"]


def test_admin_pages_show_navigation_panel(browser, make_user):
    """REQ-BE-072: every admin page shows the panel with its own section active; the personal menu only has 'Admin'."""
    person, _ = make_user()
    browser.post("/login", data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    pages = {
        "/admin": "/admin",
        f"/admin/user/{person['id']}": "/admin",
        "/admin/user/new": "/admin",
        "/admin/afvalwijzer": "/admin/afvalwijzer",
        "/admin/google-calendar-api": "/admin/google-calendar-api",
        "/admin/ai": "/admin/ai",
        "/admin/ai/log": "/admin/ai",
        "/admin/ai/costs": "/admin/ai",
        "/admin/ai/prices": "/admin/ai",
        "/admin/upgrades": "/admin/upgrades",
    }
    for path, section in pages.items():
        html = browser.get(path).text
        nav = html.split('<nav class="admin-nav"', 1)[1].split("</nav>", 1)[0]
        for href in ADMIN_SECTIONS:
            assert f'href="{href}"' in nav, (path, href)
        active = [href for href in ADMIN_SECTIONS if f'href="{href}" class="active"' in nav]
        assert active == [section], path

    menu = browser.get("/dashboard").text.split('id="personal-dropdown"', 1)[1].split("</div>", 1)[0]
    assert 'href="/admin"' in menu
    for href in ADMIN_SECTIONS[1:]:
        assert f'href="{href}"' not in menu
    for path in ["/dashboard", "/tasks", "/agenda", "/profile"]:
        assert "admin-nav" not in browser.get(path).text, path


def test_regular_user_is_kept_out_of_admin_pages(browser, make_user):
    person, _ = make_user()
    browser.post("/login", data={"username": person["username"], "password": "geheim-123"})
    for path in ["/admin", "/admin/ai", "/admin/ai/log", "/admin/ai/costs", "/admin/ai/prices"]:
        response = browser.get(path)
        assert response.status_code == 303
        assert response.headers["location"] == "/dashboard"


def test_scripts_are_versioned_by_content(browser, make_user):
    """After an update the browser must fetch changed scripts instead of using a cached copy."""
    import hashlib
    import re
    from pathlib import Path

    person, _ = make_user()
    browser.post("/login", data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    html = browser.get(f"/admin/user/{person['id']}").text
    script = Path(__file__).resolve().parent.parent / "app" / "static" / "js" / "admin_user_detail.js"
    digest = hashlib.sha256(script.read_bytes()).hexdigest()[:10]
    assert f'src="/static/js/admin_user_detail.js?v={digest}"' in html
    # Every local script and stylesheet carries a version.
    assert not re.search(r'(src|href)="/static/(js|css)/[^"?]+"', html)


def test_ai_settings_page_shows_debug_notice(browser):
    """REQ-BE-092: the settings page warns that the debug log makes conversations readable."""
    browser.post("/login", data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    page = browser.get("/admin/ai").text
    assert "kunnen beheerders de chatberichten" in page
    for path in ["/admin/ai/log", "/admin/ai/costs", "/admin/ai/prices"]:
        assert browser.get(path).status_code == 200, path
