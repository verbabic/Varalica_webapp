import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tests.test_ui_translations as translations

I18N = ROOT / "static" / "i18n.js"
SKIP = {"ASSET_REVIEW", "NOT_UI_TEXT", "NEW_FEATURE_PENDING_IMPLEMENTATION"}


def main() -> None:
    text = I18N.read_text(encoding="utf-8")
    match = re.search(r"const UI_PACKS = (\{.*?\});\nconst sourceToKey", text, re.S)
    if not match:
        raise SystemExit("UI_PACKS block was not found")
    packs = json.loads(match.group(1))
    expanded = []
    for row in translations.load_catalog():
        key = str(row["key"])
        status = str(row.get("status") or "")
        if status in SKIP and not key.startswith("suspicion."):
            continue
        if key.startswith("rules.expanded."):
            expanded.append(key)
        for lang, column in (("hr", "translation_hr"), ("sr", "translation_sr"), ("de", "translation_de")):
            if key not in packs[lang]:
                packs[lang][key] = str(row.get(column) or "")
        turkish = str(row.get("translation_tr") or "").strip()
        packs.setdefault("tr", {})
        if turkish:
            packs["tr"][key] = turkish
    for pack in packs.values():
        for key in ("api.room_full", "api.max_players"):
            if key in pack:
                pack[key] = pack[key].replace("8", "10")
    blob = json.dumps(packs, ensure_ascii=False, separators=(",", ":"))
    text = text[: match.start(1)] + blob + text[match.end(1) :]
    text = text.replace(
        'const UI_LANGS = ["hr", "sr", "de"];',
        'const UI_LANGS = ["hr", "sr", "de", "tr"];',
        1,
    )
    if "const EXPANDED_RULE_KEYS" not in text:
        text = text.replace(
            "const sourceToKey",
            "const EXPANDED_RULE_KEYS = " + json.dumps(expanded, ensure_ascii=False) + ";\nconst sourceToKey",
            1,
        )
    I18N.write_text(text, encoding="utf-8")
    print(f"hr={len(packs['hr'])} tr={len(packs['tr'])} expanded={len(expanded)}")
    print(packs["hr"]["api.max_players"])
    print(packs["tr"]["api.room_full"])


if __name__ == "__main__":
    main()
