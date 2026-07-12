import requests
from icalendar import Calendar


def normalize_ical_url(url: str) -> str:
    url = url.strip()
    if url.startswith("webcal://"):
        return "https://" + url[len("webcal://") :]
    return url


def validate_ical_feed(url: str) -> None:
    fetch_url = normalize_ical_url(url)
    response = requests.get(fetch_url, timeout=20)
    response.raise_for_status()
    Calendar.from_ical(response.content)

