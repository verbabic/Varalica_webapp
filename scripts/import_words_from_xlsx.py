from __future__ import annotations

import argparse
import pprint
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


EXPECTED_COLUMNS = ["category_key", "word_sr", "hint_sr", "word_hr", "hint_hr"]
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


def hints_for(category: str, hr: str, sr: str, hint_hr: str, hint_sr: str) -> list[str]:
    hints = list(dict.fromkeys(split_hints(hint_hr) + split_hints(hint_sr)))
    return hints[:4]


def difficulty_for(index: int) -> str:
    if index % 10 in {0, 7}:
        return "hard"
    if index % 3 == 0:
        return "easy"
    return "normal"


def load_entries(path: Path) -> tuple[str, list[dict], list[tuple[int, list[str]]], dict[str, int], list[tuple[int, list[str]]]]:
    sheet_name, rows = read_xlsx_rows(path)
    if not rows:
        raise ValueError("Workbook has no rows.")
    header = (rows[0] + [""] * len(EXPECTED_COLUMNS))[: len(EXPECTED_COLUMNS)]
    if header != EXPECTED_COLUMNS:
        raise ValueError(f"Unexpected columns: {header}. Expected: {EXPECTED_COLUMNS}")

    entries: list[dict] = []
    missing_rows: list[tuple[int, list[str]]] = []
    category_counts: dict[str, int] = defaultdict(int)
    id_counts: dict[str, int] = defaultdict(int)
    for row_number, row in enumerate(rows[1:], start=2):
        cells = (row + [""] * len(EXPECTED_COLUMNS))[: len(EXPECTED_COLUMNS)]
        cells = [cell.strip() for cell in cells]
        if not any(cells):
            continue
        if any(not cell for cell in cells):
            missing_rows.append((row_number, cells))
            continue
        if is_excluded_category(cells[0]):
            skipped_rows.append((row_number, cells))
            continue

        category = normalize_category(cells[0])
        category_counts[category] += 1
        id_counts[category] += 1
        hints = hints_for(category, cells[3], cells[1], cells[4], cells[2])
        entries.append(
            {
                "id": f"{slug(category)}_{id_counts[category]:03d}",
                "hr": cells[3],
                "sr": cells[1],
                "category": category,
                "difficulty": difficulty_for(len(entries) + 1),
                "hint_pool": hints[:4],
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
        pair = (hr.casefold(), sr.casefold())
        if pair in pairs:
            result.warn(word_id, "word", f"Duplicate word pair: {{hr}} / {{sr}} also used by {{pairs[pair]}}")
        else:
            pairs[pair] = word_id

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
    if selected_category == DEFAULT_CATEGORY:
        return STARTER_WORDS
    filtered_words = [word for word in STARTER_WORDS if word["category"] == selected_category]
    return filtered_words or STARTER_WORDS
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    sheet_name, entries, missing_rows, category_counts, skipped_rows = load_entries(args.source)
    duplicates = duplicate_report(entries)

    print(f"Sheet: {sheet_name}")
    print(f"Columns: {', '.join(EXPECTED_COLUMNS)}")
    print(f"Excel data rows read: {len(entries) + len(missing_rows) + len(skipped_rows)}")
    print(f"Imported entries: {len(entries)}")
    print(f"Rows with missing required values: {len(missing_rows)}")
    if missing_rows:
        for row_number, cells in missing_rows[:10]:
            print(f"- row {row_number}: {cells}")
    print(f"Balkan rows found/excluded: {len(skipped_rows)}")
    print(f"Rows skipped for technical/data-quality reasons: {len(missing_rows)}")
    for row_number, cells in skipped_rows[:20]:
        print(f"- skipped row {row_number}: {cells}")
    print("Category counts:")
    for category in WORD_CATEGORIES:
        print(f"- {category}: {category_counts.get(category, 0)}")
    print("Duplicate checks:")
    for name, values in duplicates.items():
        print(f"- {name}: {len(values)}")
    for label, fields in (("duplicate_pairs", ("hr", "sr")), ("duplicate_sr", ("sr",)), ("duplicate_hr", ("hr",))):
        details = duplicate_details(entries, fields)
        if details:
            print(f"{label} details:")
            for detail in details[:25]:
                print(f"- {detail}")

    invalid_categories = sorted(set(category_counts) - set(WORD_CATEGORIES))
    if invalid_categories:
        raise SystemExit(f"Invalid categories: {invalid_categories}")
    if missing_rows:
        raise SystemExit("Missing required values detected; not writing output.")

    if args.write:
        args.output.write_text(words_py_text(entries), encoding="utf-8", newline="\n")
        print(f"Wrote {args.output}")
    else:
        print("Dry run only. Pass --write to update words.py.")


if __name__ == "__main__":
    main()
