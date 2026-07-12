"""Low-level Google Calendar API calls using requests (no google-auth libs needed)."""

import logging
from urllib.parse import urlencode, quote

import requests

logger = logging.getLogger(__name__)

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"
_CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"
_SCOPES = "https://www.googleapis.com/auth/calendar.readonly"

GOOGLE_COLORS: dict[str, dict] = {
    "1":  {"name": "Lavendel",  "hex": "#7986CB"},
    "2":  {"name": "Salie",     "hex": "#33B679"},
    "3":  {"name": "Druif",     "hex": "#8E24AA"},
    "4":  {"name": "Flamingo",  "hex": "#E67C73"},
    "5":  {"name": "Banaan",    "hex": "#F6BF26"},
    "6":  {"name": "Mandarijn", "hex": "#F4511E"},
    "7":  {"name": "Pauw",      "hex": "#039BE5"},
    "8":  {"name": "Grafiet",   "hex": "#616161"},
    "9":  {"name": "Bosbes",    "hex": "#3F51B5"},
    "10": {"name": "Basilicum", "hex": "#0B8043"},
    "11": {"name": "Tomaat",    "hex": "#D50000"},
}


class SyncTokenExpiredError(Exception):
    pass


def get_auth_url(client_id: str, redirect_uri: str, state: str) -> str:
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": _SCOPES,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


def exchange_code(client_id: str, client_secret: str, redirect_uri: str, code: str) -> dict:
    resp = requests.post(_TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code,
        "grant_type": "authorization_code",
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    resp = requests.post(_TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_userinfo(access_token: str) -> dict:
    resp = requests.get(
        _USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def list_calendars(access_token: str) -> list[dict]:
    resp = requests.get(
        f"{_CALENDAR_BASE}/users/me/calendarList",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"minAccessRole": "reader"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("items", [])


def fetch_events(
    access_token: str,
    calendar_id: str,
    sync_token: str | None = None,
    time_min: str | None = None,
) -> tuple[list[dict], str | None]:
    """Fetch events using Google incremental sync.

    Returns (items, next_sync_token).
    Raises SyncTokenExpiredError when the stored sync token has expired (HTTP 410).
    """
    params: dict = {"singleEvents": "true", "maxResults": "2500"}
    if sync_token:
        params["syncToken"] = sync_token
    elif time_min:
        params["timeMin"] = time_min

    items: list[dict] = []
    next_sync_token: str | None = None
    encoded_id = quote(calendar_id, safe="")

    while True:
        resp = requests.get(
            f"{_CALENDAR_BASE}/calendars/{encoded_id}/events",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
            timeout=30,
        )

        if resp.status_code == 410:
            raise SyncTokenExpiredError("Sync token expired")

        resp.raise_for_status()
        data = resp.json()
        items.extend(data.get("items", []))

        page_token = data.get("nextPageToken")
        next_sync_token = data.get("nextSyncToken", next_sync_token)

        if not page_token:
            break
        params["pageToken"] = page_token
        params.pop("syncToken", None)

    return items, next_sync_token
