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

    for path in ["/dashboard", "/admin", "/admin/upgrades"]:
        assert browser.get(path).status_code == 200, path

    browser.get("/logout")
    assert browser.get("/dashboard").status_code == 303


def test_regular_user_is_kept_out_of_admin_pages(browser, make_user):
    person, _ = make_user()
    browser.post("/login", data={"username": person["username"], "password": "geheim-123"})
    response = browser.get("/admin")
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
