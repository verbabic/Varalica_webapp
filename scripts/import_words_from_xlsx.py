from __future__ import annotations

import argparse
import pprint
import re
import sys
import types
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


EXPECTED_COLUMNS = ["category_key", "word_sr", "hint_sr", "word_hr", "hint_hr"]
OPTIONAL_LANGUAGE_COLUMNS = ["word_de", "hint_de"]
DEFAULT_SOURCE = Path("data/Database words HR SR.xlsx")
DEFAULT_OUTPUT = Path("words.py")

DEFAULT_CATEGORY = "Sve kategorije"
WORD_CATEGORIES = [
    "Kuća",
    "Hrana",
    "Životinje",
    "Sport",
    "Škola",
    "Posao",
    "Tehnologija",
    "Putovanja",
    "Priroda",
    "Prevoz",
    "Odeća",
    "Zdravlje",
    "Zabava",
]

CATEGORY_ALIASES = {
    "kuca": "Kuća",
    "kuća": "Kuća",
    "hrana": "Hrana",
    "zivotinje": "Životinje",
    "životinje": "Životinje",
    "sport": "Sport",
    "skola": "Škola",
    "škola": "Škola",
    "posao": "Posao",
    "tehnologija": "Tehnologija",
    "putovanja": "Putovanja",
    "priroda": "Priroda",
    "prevoz": "Prevoz",
    "odjeca": "Odeća",
    "odjeća": "Odeća",
    "odeca": "Odeća",
    "odeća": "Odeća",
    "zdravlje": "Zdravlje",
    "zabava": "Zabava",
    "home": "Kuća",
    "food": "Hrana",
    "animals": "Životinje",
    "school": "Škola",
    "work": "Posao",
    "technology": "Tehnologija",
    "travel": "Putovanja",
    "nature": "Priroda",
    "transport": "Prevoz",
    "clothing": "Odeća",
    "health": "Zdravlje",
    "entertainment": "Zabava",
}

BANNED_DIRECT_HINTS = {
    "prevod", "prevođenje", "tekst", "slova", "subtitles", "subtitle",
    "sinonim", "prijevod", "definicija", "tačan naziv", "točan naziv",
    "zaštita od kiše", "osoba koja predaje", "uređaj", "predmet",
}

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def ascii_fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def slug(value: str) -> str:
    folded = ascii_fold(value)
    folded = re.sub(r"[^a-z0-9]+", "_", folded)
    return folded.strip("_") or "word"


def column_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    index = 0
    for letter in letters:
        index = index * 26 + ord(letter.upper()) - 64
    return index - 1


def read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall("m:si", NS):
        parts = [node.text or "" for node in item.findall(".//m:t", NS)]
        values.append("".join(parts))
    return values


def cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    value = cell.find("m:v", NS)
    if value is None:
        return ""
    if cell.attrib.get("t") == "s":
        return shared_strings[int(value.text or 0)].strip()
    return (value.text or "").strip()


def workbook_sheet_name(archive: zipfile.ZipFile) -> str:
    root = ET.fromstring(archive.read("xl/workbook.xml"))
    sheet = root.find(".//m:sheet", NS)
    return sheet.attrib.get("name", "Sheet1") if sheet is not None else "Sheet1"


def read_xlsx_rows(path: Path) -> tuple[str, list[list[str]]]:
    with zipfile.ZipFile(path) as archive:
        sheet_name = workbook_sheet_name(archive)
        shared_strings = read_shared_strings(archive)
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        for row in sheet.findall(".//m:sheetData/m:row", NS):
            values: dict[int, str] = {}
            for cell in row.findall("m:c", NS):
                values[column_index(cell.attrib.get("r", ""))] = cell_text(cell, shared_strings)
            if values:
                rows.append([values.get(index, "") for index in range(max(values) + 1)])
        return sheet_name, rows


def normalize_category(category_key: str) -> str:
    key = category_key.strip()
    return CATEGORY_ALIASES.get(ascii_fold(key), key)


def is_excluded_category(category_key: str) -> bool:
    return ascii_fold(category_key.strip()) == "balkan"


def split_hints(value: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"[;,|]", value) if part.strip()]
    return parts or [value.strip()]


def language_hints(value: str) -> list[str]:
    return split_hints(value)[:4]


def hints_for(category: str, hr: str, sr: str, hint_hr: str, hint_sr: str) -> list[str]:
    return language_hints(hint_hr)


def difficulty_for(index: int) -> str:
    if index % 10 in {0, 7}:
        return "hard"
    if index % 3 == 0:
        return "easy"
    return "normal"


APPROVED_COLUMNS = [
    "category_key",
    "word_sr",
    "hint_sr",
    "word_hr",
    "hint_hr",
    "word_de",
    "hint_de",
    "word_tr",
    "hint_tr",
]
ALLOWED_DIFFICULTIES = {"easy", "normal", "hard"}


class CatalogSyncError(RuntimeError):
    """The workbook cannot be applied without moving or dropping a catalog slot."""


def concept_pair(hr: str, sr: str) -> tuple[str, str]:
    from word_locales import _pair

    return _pair(hr, sr)


def load_approved_concepts(path: Path) -> tuple[str, list[dict]]:
    sheet_name, rows = read_xlsx_rows(path)
    if not rows:
        raise CatalogSyncError(f"{path} has no rows.")
    header = [cell.strip() for cell in rows[0]]
    missing_columns = [name for name in APPROVED_COLUMNS if name not in header]
    if missing_columns:
        raise CatalogSyncError(
            f"{path} is missing required columns: {', '.join(missing_columns)}. Found: {header}"
        )
    index = {name: position for position, name in enumerate(header)}
    concepts: list[dict] = []
    seen: dict[tuple[str, str], int] = {}
    blanks: list[str] = []
    bad_categories: list[str] = []
    for row_number, row in enumerate(rows[1:], start=2):
        def cell(name: str, row: list[str] = row) -> str:
            position = index[name]
            return row[position].strip() if position < len(row) else ""

        values = {name: cell(name) for name in APPROVED_COLUMNS}
        if not any(values.values()):
            continue
        empty = [name for name in APPROVED_COLUMNS if not values[name]]
        if empty:
            blanks.append(f"row {row_number}: empty {', '.join(empty)}")
            continue
        category = normalize_category(values["category_key"])
        if category not in WORD_CATEGORIES:
            bad_categories.append(f"row {row_number}: {values['category_key']!r}")
            continue
        pair = concept_pair(values["word_hr"], values["word_sr"])
        if pair in seen:
            raise CatalogSyncError(
                "Workbook has duplicate concepts and was not imported: "
                f"rows {seen[pair]} and {row_number} "
                f"({values['word_hr']} / {values['word_sr']})."
            )
        hints = {
            "hint_hr": language_hints(values["hint_hr"]),
            "hint_sr": language_hints(values["hint_sr"]),
            "hint_de": language_hints(values["hint_de"]),
            "hint_tr": language_hints(values["hint_tr"]),
        }
        if any(not hint_list or any(not hint for hint in hint_list) for hint_list in hints.values()):
            blanks.append(f"row {row_number}: empty hint after splitting")
            continue
        seen[pair] = row_number
        concepts.append(
            {
                "row": row_number,
                "pair": pair,
                "category": category,
                "hr": values["word_hr"],
                "sr": values["word_sr"],
                "de": values["word_de"],
                "tr": values["word_tr"],
                **hints,
            }
        )
    if blanks:
        preview = "\n".join(f"- {item}" for item in blanks[:20])
        raise CatalogSyncError(f"Workbook has blank approved fields. Nothing was written.\n{preview}")
    if bad_categories:
        preview = "\n".join(f"- {item}" for item in bad_categories[:20])
        raise CatalogSyncError(f"Workbook has categories outside the game list. Nothing was written.\n{preview}")
    if not concepts:
        raise CatalogSyncError("Workbook has no approved concepts. Nothing was written.")
    return sheet_name, concepts


def _parsed_id(word_id: str) -> tuple[str, int]:
    prefix, separator, suffix = word_id.rpartition("_")
    if not separator or not suffix.isdigit():
        raise CatalogSyncError(f"Cannot parse a stable id: {word_id}")
    return prefix, int(suffix)


def _next_id(category: str, used: set[str], counters: dict[str, int]) -> str:
    prefix = slug(category)
    number = counters.get(prefix, 0)
    while True:
        number += 1
        candidate = f"{prefix}_{number:03d}"
        if candidate not in used:
            counters[prefix] = number
            used.add(candidate)
            return candidate


def _inactive_entry(word: dict) -> dict:
    hints = word.get("hint_pool")
    if not isinstance(hints, list) or not any(str(hint).strip() for hint in hints):
        raise CatalogSyncError(f"{word.get('id')} has no hint_pool. Refusing to rewrite the catalog.")
    difficulty = word.get("difficulty")
    if difficulty not in ALLOWED_DIFFICULTIES:
        raise CatalogSyncError(f"{word.get('id')} has invalid difficulty {difficulty!r}.")
    return {
        "id": word["id"],
        "hr": word["hr"],
        "sr": word["sr"],
        "category": word["category"],
        "difficulty": difficulty,
        "hint_pool": list(hints),
        "active": False,
    }


def _active_entry(word_id: str, difficulty: str, concept: dict) -> dict:
    hint_hr = list(concept["hint_hr"])
    return {
        "id": word_id,
        "hr": concept["hr"],
        "sr": concept["sr"],
        "de": concept["de"],
        "tr": concept["tr"],
        "category": concept["category"],
        "difficulty": difficulty,
        "hint_hr": hint_hr,
        "hint_sr": list(concept["hint_sr"]),
        "hint_de": list(concept["hint_de"]),
        "hint_tr": list(concept["hint_tr"]),
        "hint_pool": list(hint_hr),
        "active": True,
    }


def synchronize_catalog(starter: list[dict], concepts: list[dict]) -> tuple[list[dict], dict]:
    by_pair = {concept["pair"]: concept for concept in concepts}
    if len(by_pair) != len(concepts):
        raise CatalogSyncError("Approved concepts are not unique. Nothing was written.")
    claimed: dict[tuple[str, str], int] = {}
    catalog: list[dict] = []
    updated = 0
    inactive_absent = 0
    inactive_duplicate = 0
    category_changes: list[str] = []
    seen_ids: set[str] = set()
    for index, word in enumerate(starter):
        word_id = str(word.get("id") or "").strip()
        if not word_id:
            raise CatalogSyncError(f"Existing catalog index {index} has no id. Nothing was written.")
        if word_id in seen_ids:
            raise CatalogSyncError(f"Existing id {word_id} is duplicated. Nothing was written.")
        seen_ids.add(word_id)
        _parsed_id(word_id)
        pair = concept_pair(str(word.get("hr") or ""), str(word.get("sr") or ""))
        concept = by_pair.get(pair)
        if concept is not None and pair not in claimed:
            if word.get("difficulty") not in ALLOWED_DIFFICULTIES:
                raise CatalogSyncError(f"{word_id} has invalid difficulty {word.get('difficulty')!r}.")
            if concept["category"] != word.get("category"):
                category_changes.append(f"{word_id} index {index}: {word.get('category')} -> {concept['category']}")
            catalog.append(_active_entry(word_id, str(word["difficulty"]), concept))
            claimed[pair] = index
            updated += 1
        else:
            catalog.append(_inactive_entry(word))
            if concept is None:
                inactive_absent += 1
            else:
                inactive_duplicate += 1
    if [entry["id"] for entry in catalog] != [word["id"] for word in starter]:
        raise CatalogSyncError("Existing indexes or ids changed. Nothing was written.")
    counters: dict[str, int] = {}
    for entry in catalog:
        prefix, number = _parsed_id(entry["id"])
        counters[prefix] = max(counters.get(prefix, 0), number)
    used_ids = set(seen_ids)
    appended_ids: list[str] = []
    for concept in concepts:
        if concept["pair"] in claimed:
            continue
        word_id = _next_id(concept["category"], used_ids, counters)
        catalog.append(_active_entry(word_id, difficulty_for(len(catalog) + 1), concept))
        claimed[concept["pair"]] = len(catalog) - 1
        appended_ids.append(word_id)
    active_entries = [entry for entry in catalog if entry["active"]]
    active_pairs = [concept_pair(entry["hr"], entry["sr"]) for entry in active_entries]
    if len(active_pairs) != len(set(active_pairs)):
        raise CatalogSyncError("Active catalog contains duplicate concepts. Nothing was written.")
    if set(active_pairs) != set(by_pair):
        raise CatalogSyncError(
            "Active catalog does not match the workbook "
            f"({len(set(by_pair) - set(active_pairs))} missing, "
            f"{len(set(active_pairs) - set(by_pair))} unapproved). Nothing was written."
        )
    if len({entry["id"] for entry in catalog}) != len(catalog):
        raise CatalogSyncError("Catalog ids are not unique. Nothing was written.")
    report = {
        "preserved_positions": len(starter),
        "updated_in_place": updated,
        "inactive_absent": inactive_absent,
        "inactive_duplicate": inactive_duplicate,
        "appended": len(appended_ids),
        "appended_ids": appended_ids,
        "physical": len(catalog),
        "active": len(active_entries),
        "inactive": len(catalog) - len(active_entries),
        "category_changes": category_changes,
    }
    return catalog, report


def load_entries(path: Path) -> tuple[str, list[dict], list[tuple[int, list[str]]], dict[str, int], list[tuple[int, list[str]]]]:
    """Read rows in worksheet order. This does not preserve catalog indexes.

    Catalog updates go through synchronize_catalog(), which keeps existing slots.
    """
    sheet_name, rows = read_xlsx_rows(path)
    if not rows:
        raise ValueError("Workbook has no rows.")
    header = [cell.strip() for cell in rows[0]]
    if header[: len(EXPECTED_COLUMNS)] != EXPECTED_COLUMNS:
        raise ValueError(f"Unexpected columns: {header}. Expected: {EXPECTED_COLUMNS}")
    has_german = header[len(EXPECTED_COLUMNS): len(EXPECTED_COLUMNS) + 2] == OPTIONAL_LANGUAGE_COLUMNS

    entries: list[dict] = []
    missing_rows: list[tuple[int, list[str]]] = []
    skipped_rows: list[tuple[int, list[str]]] = []
    category_counts: dict[str, int] = defaultdict(int)
    id_counts: dict[str, int] = defaultdict(int)
    for row_number, row in enumerate(rows[1:], start=2):
        width = len(EXPECTED_COLUMNS) + (2 if has_german else 0)
        cells = (row + [""] * width)[:width]
        cells = [cell.strip() for cell in cells]
        if not any(cells[: len(EXPECTED_COLUMNS)]):
            continue
        if any(not cell for cell in cells[: len(EXPECTED_COLUMNS)]):
            missing_rows.append((row_number, cells))
            continue
        if is_excluded_category(cells[0]):
            skipped_rows.append((row_number, cells))
            continue

        category = normalize_category(cells[0])
        category_counts[category] += 1
        id_counts[category] += 1
        hint_hr = language_hints(cells[4])
        hint_sr = language_hints(cells[2])
        hint_de = language_hints(cells[6]) if has_german and len(cells) > 6 else []
        entries.append(
            {
                "id": f"{slug(category)}_{id_counts[category]:03d}",
                "hr": cells[3],
                "sr": cells[1],
                "de": cells[5] if has_german and len(cells) > 5 else "",
                "category": category,
                "difficulty": difficulty_for(len(entries) + 1),
                "hint_hr": hint_hr,
                "hint_sr": hint_sr,
                "hint_de": hint_de,
                "hint_pool": hint_hr[:4],
            }
        )
    return sheet_name, entries, missing_rows, dict(category_counts), []


def duplicate_report(entries: list[dict]) -> dict[str, list]:
    word_pairs = Counter((entry["hr"].casefold(), entry["sr"].casefold()) for entry in entries)
    sr_words = Counter(entry["sr"].casefold() for entry in entries)
    hr_words = Counter(entry["hr"].casefold() for entry in entries)
    hint_values = Counter(hint.casefold() for entry in entries for hint in entry["hint_pool"])
    return {
        "duplicate_pairs": [item for item, count in word_pairs.items() if count > 1],
        "duplicate_sr": [item for item, count in sr_words.items() if count > 1],
        "duplicate_hr": [item for item, count in hr_words.items() if count > 1],
        "duplicate_hints_over_10": [item for item, count in hint_values.items() if count > 10],
    }


def duplicate_details(entries: list[dict], field_names: tuple[str, ...]) -> list[str]:
    grouped: defaultdict[tuple[str, ...], list[dict]] = defaultdict(list)
    for entry in entries:
        key = tuple(entry[field_name].casefold() for field_name in field_names)
        grouped[key].append(entry)
    details: list[str] = []
    for _, items in grouped.items():
        if len(items) > 1:
            details.append(
                "; ".join(
                    f"{item['id']} {item['category']} {item['hr']} / {item['sr']}"
                    for item in items
                )
            )
    return details


def words_py_text(entries: list[dict]) -> str:
    data = pprint.pformat(entries, width=120, sort_dicts=False)
    return f'''from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
import random
import unicodedata

DEFAULT_CATEGORY = "Sve kategorije"
WORD_CATEGORIES = {WORD_CATEGORIES!r}
ALLOWED_CATEGORIES = [DEFAULT_CATEGORY, *WORD_CATEGORIES]
ALLOWED_DIFFICULTIES = {{"easy", "normal", "hard"}}

SUSPICIOUS_PREFIXES = (
    "svakodnevni ", "svakodnevna ", "svakodnevno ",
    "profesionalni ", "profesionalna ", "profesionalno ",
    "mali ", "mala ", "malo ", "veliki ", "velika ", "veliko ",
    "moderni ", "moderna ", "moderno ", "zanimljiv ", "zanimljiva ",
    "poseban ", "posebna ", "brzi ", "brza ", "brzo ",
)

BANNED_DIRECT_HINTS = {{
    "prevod", "prevođenje", "tekst", "slova", "subtitles", "subtitle",
    "sinonim", "prijevod", "definicija", "tačan naziv", "točan naziv",
    "zaštita od kiše", "osoba koja predaje", "uređaj", "predmet",
}}

ASCII_DIACRITIC_EXPECTATIONS = {{
    "kuca": "kuća", "vozac": "vozač", "cebe": "ćebe", "djak": "đak",
    "zivotinja": "životinja", "macka": "mačka", "casa": "čaša",
    "rucak": "ručak", "suma": "šuma", "zaba": "žaba", "noz": "nož",
    "sesir": "šešir", "kisobran": "kišobran", "carapa": "čarapa",
}}


@dataclass
class ValidationIssue:
    word_id: str
    field: str
    message: str


@dataclass
class ValidationResult:
    structural_errors: list[ValidationIssue] = field(default_factory=list)
    quality_warnings: list[ValidationIssue] = field(default_factory=list)

    def add(self, word_id: str, field: str, message: str) -> None:
        self.structural_errors.append(ValidationIssue(word_id, field, message))

    def warn(self, word_id: str, field: str, message: str) -> None:
        self.quality_warnings.append(ValidationIssue(word_id, field, message))


def ascii_fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


STARTER_WORDS = {data}


def is_active_word(word: dict) -> bool:
    return bool(word.get("active", True))


def validate_words(words: list[dict], strict: bool = False) -> ValidationResult:
    result = ValidationResult()

    ids: set[str] = set()
    pairs: dict[tuple[str, str], str] = {{}}
    for word in words:
        word_id = str(word.get("id", "")).strip()
        if not word_id:
            result.add("missing-id", "id", "Missing id")
            continue
        if word_id in ids:
            result.add(word_id, "id", "Duplicate id")
        ids.add(word_id)

        for field_name in ("hr", "sr", "category", "difficulty", "hint_pool"):
            if field_name not in word:
                result.add(word_id, field_name, "Missing field")
            if field_name != "hint_pool" and not str(word.get(field_name, "")).strip():
                result.add(word_id, field_name, "Empty field")

        hr = str(word.get("hr", "")).strip()
        sr = str(word.get("sr", "")).strip()
        if is_active_word(word):
            pair = (hr.casefold(), sr.casefold())
            if pair in pairs:
                result.add(word_id, "word", f"Duplicate active word pair: {{hr}} / {{sr}} also used by {{pairs[pair]}}")
            else:
                pairs[pair] = word_id
            for field_name in ("de", "tr"):
                if not str(word.get(field_name, "")).strip():
                    result.add(word_id, field_name, "Empty field")
            for field_name in ("hint_hr", "hint_sr", "hint_de", "hint_tr"):
                localized_hints = word.get(field_name)
                if not isinstance(localized_hints, list) or not any(str(hint).strip() for hint in localized_hints):
                    result.add(word_id, field_name, "Missing language hint")

        category = str(word.get("category", ""))
        if category not in WORD_CATEGORIES:
            result.add(word_id, "category", f"Invalid category: {{category}}")

        difficulty = str(word.get("difficulty", ""))
        if difficulty not in ALLOWED_DIFFICULTIES:
            result.add(word_id, "difficulty", f"Invalid difficulty: {{difficulty}}")

        hints = word.get("hint_pool", [])
        if not isinstance(hints, list) or not 1 <= len(hints) <= 4:
            result.add(word_id, "hint_pool", "hint_pool must contain 1-4 hints")
            hints = []
        for hint in hints:
            hint_text = str(hint).strip()
            if not hint_text:
                result.add(word_id, "hint_pool", "Empty hint")
                continue
            hint_fold = ascii_fold(hint_text)
            if hint_fold in {{ascii_fold(hr), ascii_fold(sr)}}:
                result.warn(word_id, "hint_pool", f"Hint reveals exact word: {{hint_text}}")
            if hint_fold in BANNED_DIRECT_HINTS:
                result.warn(word_id, "hint_pool", f"Direct banned hint: {{hint_text}}")

        for field_name in ("hr", "sr"):
            text = str(word.get(field_name, "")).strip()
            lower = text.casefold()
            if lower.startswith(SUSPICIOUS_PREFIXES):
                result.warn(word_id, field_name, f"Suspicious generated phrase: {{text}}")
            folded = ascii_fold(text)
            if folded in ASCII_DIACRITIC_EXPECTATIONS and not any(ch in text for ch in "čćšđžČĆŠĐŽ"):
                result.warn(word_id, field_name, f"Suspicious missing diacritics: {{text}}")

    if strict and result.structural_errors:
        details = "\\n".join(f"- {{issue.word_id}} [{{issue.field}}]: {{issue.message}}" for issue in result.structural_errors[:30])
        raise ValueError(f"Word validation failed with {{len(result.structural_errors)}} structural issue(s):\\n{{details}}")
    return result


def duplicate_word_warnings(words: list[dict]) -> list[str]:
    sr_words: defaultdict[str, list[str]] = defaultdict(list)
    hr_words: defaultdict[str, list[str]] = defaultdict(list)
    pairs: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
    for word in words:
        if not word.get("active", True):
            continue
        word_id = word["id"]
        sr_words[str(word.get("sr", "")).casefold()].append(word_id)
        hr_words[str(word.get("hr", "")).casefold()].append(word_id)
        pairs[(str(word.get("hr", "")).casefold(), str(word.get("sr", "")).casefold())].append(word_id)
    warnings: list[str] = []
    for label, grouped in (("Duplicate SR word", sr_words), ("Duplicate HR word", hr_words), ("Duplicate HR/SR pair", pairs)):
        for value, ids in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True):
            if value and len(ids) > 1:
                warnings.append(f"{{label}} repeated {{len(ids)}} times: {{value}} -> {{', '.join(ids[:8])}}")
    return warnings


def hint_repetition_warnings(words: list[dict]) -> list[str]:
    exact: defaultdict[tuple[str, ...], list[str]] = defaultdict(list)
    first_three: defaultdict[tuple[str, ...], list[str]] = defaultdict(list)
    for word in words:
        if not word.get("active", True):
            continue
        hints = tuple(word.get("hint_pool", []))
        exact[hints].append(word["id"])
        first_three[hints[:3]].append(word["id"])
    warnings: list[str] = []
    for hints, ids in sorted(exact.items(), key=lambda item: len(item[1]), reverse=True):
        if len(ids) > 3:
            warnings.append(f"Exact hint_pool repeated {{len(ids)}} times: {{hints}} -> {{', '.join(ids[:8])}}")
    for hints, ids in sorted(first_three.items(), key=lambda item: len(item[1]), reverse=True):
        if len(ids) > 4:
            warnings.append(f"First 3 hints repeated {{len(ids)}} times: {{hints}} -> {{', '.join(ids[:8])}}")
    return warnings


def random_hint(word: dict) -> str:
    hints = word.get("hint_pool") or []
    if hints:
        return random.choice(hints)
    return word.get("hint", "Slušaj asocijacije i uklopi se.")


validate_words(STARTER_WORDS, strict=True)


def normalize_category(category: str | None) -> str:
    if category in WORD_CATEGORIES:
        return category
    return DEFAULT_CATEGORY


def words_for_category(category: str | None) -> list[dict]:
    selected_category = normalize_category(category)
    active_words = [word for word in STARTER_WORDS if is_active_word(word)]
    if selected_category == DEFAULT_CATEGORY:
        return active_words
    filtered_words = [word for word in active_words if word["category"] == selected_category]
    return filtered_words or active_words
'''


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize words.py with the approved workbook.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    try:
        sheet_name, concepts = load_approved_concepts(args.source)
        from words import STARTER_WORDS

        catalog, report = synchronize_catalog(list(STARTER_WORDS), concepts)
        repeated, _repeated_report = synchronize_catalog(catalog, concepts)
        if repeated != catalog:
            raise CatalogSyncError("Repeating the import changed the catalog. Nothing was written.")
        generated = words_py_text(catalog)
        preview = types.ModuleType("words_preview")
        preview.__file__ = str(args.output)
        sys.modules["words_preview"] = preview
        try:
            exec(compile(generated, str(args.output), "exec"), preview.__dict__)
        finally:
            sys.modules.pop("words_preview", None)
        if preview.STARTER_WORDS != catalog:
            raise CatalogSyncError("Generated words.py does not round-trip. Nothing was written.")
    except CatalogSyncError as exc:
        raise SystemExit(str(exc)) from exc

    print(f"Sheet: {sheet_name}")
    print(f"Workbook concepts: {len(concepts)}")
    print(f"Preserved positions: {report['preserved_positions']}")
    print(f"Updated in place: {report['updated_in_place']}")
    print(f"Inactive, absent from workbook: {report['inactive_absent']}")
    print(f"Inactive, redundant duplicates: {report['inactive_duplicate']}")
    print(f"Appended: {report['appended']}")
    print(f"Physical records: {report['physical']}")
    print(f"Active records: {report['active']}")
    print(f"Inactive records: {report['inactive']}")
    print(f"Category changes: {len(report['category_changes'])}")
    for change in report["category_changes"]:
        print(f"- {change}")
    print("Repeated import check: unchanged")
    if args.write:
        args.output.write_text(generated, encoding="utf-8", newline="\n")
        print(f"Wrote {args.output}")
    else:
        print("Dry run only. Pass --write to update words.py.")


if __name__ == "__main__":
    main()
