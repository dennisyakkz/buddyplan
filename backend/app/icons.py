import json
from functools import lru_cache
from pathlib import Path

ICONS_FILE = Path(__file__).resolve().parent / "static" / "data" / "material-icons.json"

DEFAULT_ICON = "md:check_circle"

# Old short names / FA ids → Material (or default). Unknown → DEFAULT_ICON.
LEGACY_ICON_MAP = {
    "toothbrush": "md:dentistry",
    "shower": "md:shower",
    "food": "md:restaurant",
    "home": "md:home",
    "book": "md:menu_book",
    "music": "md:music_note",
    "walk": "md:directions_walk",
    "clothes": "md:checkroom",
    "water": "md:water_drop",
    "bed": "md:bed",
    "check": "md:check_circle",
    "default": DEFAULT_ICON,
    "fas:trash": "custom:kliko-restafval",
    "fas:circle-check": DEFAULT_ICON,
}


@lru_cache
def load_icons() -> list[dict]:
    if not ICONS_FILE.is_file():
        raise FileNotFoundError(
            f"Icon catalog missing: {ICONS_FILE}. Ensure app/static/data/material-icons.json is included in the image."
        )
    with open(ICONS_FILE, encoding="utf-8") as f:
        return json.load(f)


def normalize_icon_id(icon_id: str | None) -> str:
    if not icon_id:
        return DEFAULT_ICON
    raw = icon_id.strip()
    if not raw:
        return DEFAULT_ICON
    if raw.startswith("md:") or raw.startswith("custom:"):
        return raw
    if raw in LEGACY_ICON_MAP:
        return LEGACY_ICON_MAP[raw]
    # Unknown / old fas:* → safe default (no DB migration)
    return DEFAULT_ICON
