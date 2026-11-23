from __future__ import annotations

import json
from pathlib import Path

from scripts.import_words_from_xlsx import language_hints, read_xlsx_rows


BASE_DIR = Path(__file__).resolve().parent
SOURCE = BASE_DIR / "data" / "Database words HR SR.xlsx"
PROPOSED_GAPS = BASE_DIR / "data" / "proposed_locale_gaps.json"
LOCALE_FIELDS = ("de", "tr", "hint_de", "hint_tr")


_HOMOGLYPHS = str.maketrans({
    "а": "a",
    "е": "e",
    "о": "o",
    "с": "c",
    "і": "i",
    "ї": "i",
    "р": "p",
    "у": "y",
    "х": "x",
    "ѕ": "s",
})


def _pair(hr: str, sr: str) -> tuple[str, str]:
    def fold(value: str) -> str:
        return value.strip().casefold().translate(_HOMOGLYPHS)

    return (fold(hr), fold(sr))


def load_locale_overlay(path: Path = SOURCE) -> dict[tuple[str, str], dict]:
    if not path.is_file():
        return {}
    _sheet_name, rows = read_xlsx_rows(path)
    if not rows:
        return {}
    header = [cell.strip() for cell in rows[0]]
    index = {name: position for position, name in enumerate(header)}
    required = ["word_hr", "word_sr", "word_de", "hint_de", "word_tr", "hint_tr"]
    if any(name not in index for name in required):
        return {}
    overlay: dict[tuple[str, str], dict] = {}
    for row in rows[1:]:
        def cell(name: str) -> str:
            position = index[name]
            return row[position].strip() if position < len(row) else ""

        hr = cell("word_hr")
        sr = cell("word_sr")
        if not hr or not sr:
            continue
        key = _pair(hr, sr)
        if key in overlay:
            continue
        overlay[key] = {
            "de": cell("word_de"),
            "tr": cell("word_tr"),
            "hint_de": language_hints(cell("hint_de")) if cell("hint_de") else [],
            "hint_tr": language_hints(cell("hint_tr")) if cell("hint_tr") else [],
        }
    return overlay


def load_proposed_gaps(path: Path = PROPOSED_GAPS) -> dict[str, dict]:
    """Unapproved draft translations. Gameplay must not use them."""
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    words = payload.get("words") if isinstance(payload, dict) else None
    return words if isinstance(words, dict) else {}


LOCALE_OVERLAY = load_locale_overlay()
PROPOSED_LOCALE_GAPS = load_proposed_gaps()


def _fill_empty(merged: dict, extra: dict | None) -> None:
    if not extra:
        return
    for field in LOCALE_FIELDS:
        if merged.get(field):
            continue
        value = extra.get(field)
        if value:
            merged[field] = value


def with_locales(word: dict | None) -> dict | None:
    if not isinstance(word, dict):
        return word
    merged = dict(word)
    _fill_empty(merged, LOCALE_OVERLAY.get(_pair(str(word.get("hr") or ""), str(word.get("sr") or ""))))
    return merged


def locale_counts() -> dict[str, int]:
    filled = {field: 0 for field in ("de", "tr")}
    for entry in LOCALE_OVERLAY.values():
        if entry.get("de"):
            filled["de"] += 1
        if entry.get("tr"):
            filled["tr"] += 1
    return {"pairs": len(LOCALE_OVERLAY), **filled}
