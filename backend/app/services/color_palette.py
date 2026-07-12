"""Brandbook agenda color labels (light mode only for web)."""

from __future__ import annotations

import re

BRAND_LABELS: tuple[str, ...] = (
    "rood",
    "oranje",
    "geel",
    "groen",
    "blauw",
    "teal",
    "paars",
    "bruin",
)

_LABEL_BG_HEX: dict[str, str] = {
    "rood": "#FED7D7",
    "oranje": "#FEEBC8",
    "geel": "#FEFCBF",
    "groen": "#C6F6D5",
    "blauw": "#EBF8FF",
    "teal": "#E6FFFA",
    "paars": "#EBF4FF",
    "bruin": "#EDF2F7",
}

_LEGACY_HEX_MAP: dict[str, str] = {
    "#e74c3c": "rood",
    "#e67e22": "oranje",
    "#f1c40f": "geel",
    "#27ae60": "groen",
    "#1abc9c": "teal",
    "#3498db": "blauw",
    "#2980b9": "blauw",
    "#9b59b6": "paars",
    "#e91e63": "rood",
    "#795548": "bruin",
    "#607d8b": "bruin",
    "#2c3e50": "bruin",
}

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _color_distance(a: str, b: str) -> float:
    ar, ag, ab = _rgb(a)
    br, bg, bb = _rgb(b)
    return (ar - br) ** 2 + (ag - bg) ** 2 + (ab - bb) ** 2


def hex_to_label(value: str | None) -> str | None:
    """Map a hex color or existing label to the nearest brandbook label."""
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    lowered = raw.lower()
    if lowered in BRAND_LABELS:
        return lowered
    if lowered in _LEGACY_HEX_MAP:
        return _LEGACY_HEX_MAP[lowered]
    if _HEX_RE.match(raw):
        return min(_LABEL_BG_HEX, key=lambda label: _color_distance(raw, _LABEL_BG_HEX[label]))
    return None


def normalize_stored_color(value: str | None) -> str | None:
    """Normalize a stored feed/calendar color to a label string."""
    return hex_to_label(value)


def resolve_color_label(
    *,
    feed_color: str | None = None,
    event_color: str | None = None,
    google_calendar_color: str | None = None,
) -> str | None:
    """Resolve display label with event → Google calendar → feed priority."""
    for source in (event_color, google_calendar_color, feed_color):
        label = hex_to_label(source)
        if label:
            return label
    return None


def label_to_badge_classes(label: str | None) -> str:
    if label and label in BRAND_LABELS:
        return f"cal-chip agenda-badge-{label}"
    return "cal-chip"
