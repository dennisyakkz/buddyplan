import json
from functools import lru_cache
from pathlib import Path

ICONS_FILE = Path(__file__).resolve().parent / "static" / "data" / "fa-icons.json"

LEGACY_ICON_MAP = {
    "toothbrush": "fas:tooth",
    "shower": "fas:shower",
    "food": "fas:utensils",
    "home": "fas:house",
    "book": "fas:book",
    "music": "fas:music",
    "walk": "fas:person-walking",
    "clothes": "fas:shirt",
    "water": "fas:glass-water",
    "bed": "fas:bed",
    "default": "fas:circle-check",
}


@lru_cache
def load_icons() -> list[dict]:
    with open(ICONS_FILE, encoding="utf-8") as f:
        return json.load(f)


def normalize_icon_id(icon_id: str | None) -> str:
    if not icon_id:
        return LEGACY_ICON_MAP["default"]
    if icon_id.startswith("fas:"):
        return icon_id
    return LEGACY_ICON_MAP.get(icon_id, f"fas:{icon_id}")
