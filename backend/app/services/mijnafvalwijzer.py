import re
import logging
from datetime import date

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MONTHS = {
    "januari": 1, "februari": 2, "maart": 3, "april": 4,
    "mei": 5, "juni": 6, "juli": 7, "augustus": 8,
    "september": 9, "oktober": 10, "november": 11, "december": 12,
}


def _parse_housenumber(huisnummer: str) -> tuple[str, str]:
    m = re.search(r"^(\d+)(\D*)$", huisnummer.strip())
    if m:
        return m.group(1), m.group(2).strip()
    return huisnummer.strip(), ""


def _fetch_soup(postcode: str, huisnummer: str) -> BeautifulSoup:
    number, suffix = _parse_housenumber(huisnummer)
    url = f"https://www.mijnafvalwijzer.nl/nl/{postcode.strip()}/{number}/{suffix}"
    response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def _parse_events(soup: BeautifulSoup) -> list[dict]:
    events = []
    seen_uids = set()

    for item in soup.find_all("a", "wasteInfoIcon textDecorationNone"):
        waste_type = item.get("href", "").replace("#", "").replace("waste-", "")
        if waste_type in ("", "javascript:void(0);"):
            p_tag = item.find("p")
            if p_tag and p_tag.has_attr("class"):
                waste_type = p_tag["class"][0]

        p_tag = item.find("p")
        if not p_tag:
            continue

        raw_d = re.search(r"(\w+) (\d+) (\w+)( (\d+))?", p_tag.text)
        if not raw_d:
            continue

        month = MONTHS.get(raw_d.group(3), 0)
        if not month:
            continue

        year = int(raw_d.group(5)) if raw_d.group(5) else date.today().year
        try:
            event_date = date(year, month, int(raw_d.group(2)))
        except ValueError:
            continue

        descr_span = item.find("span", {"class": "afvaldescr"})
        label = descr_span.text.strip() if descr_span else waste_type

        uid = f"{event_date.isoformat()}-{waste_type}"
        if uid in seen_uids:
            continue
        seen_uids.add(uid)

        events.append({"date": event_date, "waste_type": waste_type, "label": label})

    return events


def get_afval_types(postcode: str, huisnummer: str) -> list[dict]:
    """Return unique waste types for the given address as [{waste_type, label}]."""
    soup = _fetch_soup(postcode, huisnummer)
    events = _parse_events(soup)
    seen: dict[str, str] = {}
    for event in events:
        wt = event["waste_type"]
        if wt not in seen:
            seen[wt] = event["label"]
    return [{"waste_type": k, "label": v} for k, v in seen.items()]


def get_schedule(
    postcode: str,
    huisnummer: str,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[dict]:
    """Return pickup events as [{date, waste_type, label}] sorted by date."""
    soup = _fetch_soup(postcode, huisnummer)
    events = _parse_events(soup)
    if from_date:
        events = [e for e in events if e["date"] >= from_date]
    if to_date:
        events = [e for e in events if e["date"] <= to_date]
    return sorted(events, key=lambda e: e["date"])
