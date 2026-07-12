import requests
from icalendar import Calendar

_FORCE_FULL_SINCE = "Thu, 01 Jan 1970 00:00:00 GMT"


def normalize_ical_url(url: str) -> str:
    url = url.strip()
    if url.startswith("webcal://"):
        return "https://" + url[len("webcal://") :]
    return url


def fetch_ical_response(
    url: str,
    *,
    etag: str | None = None,
    last_modified: str | None = None,
    force_full: bool = False,
) -> requests.Response:
    headers = {
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Accept": "text/calendar,*/*",
    }
    if force_full:
        headers["If-Modified-Since"] = _FORCE_FULL_SINCE
    else:
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
        elif not etag:
            # Some iCal servers (e.g. rooster.nl) return an empty 304 without
            # conditional headers; force a full response on first fetch.
            headers["If-Modified-Since"] = _FORCE_FULL_SINCE

    return requests.get(normalize_ical_url(url), headers=headers, timeout=30)


def fetch_ical_content(
    url: str,
    *,
    etag: str | None = None,
    last_modified: str | None = None,
    force_full: bool = False,
) -> bytes:
    response = fetch_ical_response(
        url,
        etag=etag,
        last_modified=last_modified,
        force_full=force_full,
    )
    if response.status_code == 304 and not response.content:
        if force_full:
            raise ValueError(
                "Agenda-server gaf geen data terug (304). Probeer later opnieuw."
            )
        response = fetch_ical_response(url, force_full=True)
    response.raise_for_status()
    if response.status_code == 304 or not response.content:
        raise ValueError(
            "Agenda-server gaf geen data terug (304). Probeer later opnieuw."
        )
    return response.content


def validate_ical_feed(url: str) -> bytes:
    content = fetch_ical_content(url, force_full=True)
    Calendar.from_ical(content)
    return content
