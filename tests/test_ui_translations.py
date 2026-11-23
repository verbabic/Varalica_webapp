import json
import re
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
I18N = (ROOT / "static" / "i18n.js").read_text(encoding="utf-8")
WORKBOOK = ROOT / "docs" / "localization" / "VARALICA_UI_TRANSLATIONS_REVIEWED_V3.xlsx"
SKIP_STATUS = {"ASSET_REVIEW", "NOT_UI_TEXT", "NEW_FEATURE_PENDING_IMPLEMENTATION"}
PLACEHOLDER = re.compile(r"\{[a-zA-Z0-9_]+\}")


def load_packs():
    match = re.search(r"const UI_PACKS = (\{.*\});\n", I18N)
    if not match:
        raise AssertionError("UI_PACKS block was not found in static/i18n.js")
    return json.loads(match.group(1))


def worksheet_rows(path):
    namespace = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as workbook:
        shared = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            root = ElementTree.fromstring(workbook.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", namespace):
                shared.append("".join(node.text or "" for node in item.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")))
        sheet = ElementTree.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in sheet.findall("m:sheetData/m:row", namespace):
            values = []
            for cell in row.findall("m:c", namespace):
                ref = cell.attrib.get("r", "A1")
                column = 0
                for char in ref:
                    if char.isalpha():
                        column = column * 26 + ord(char.upper()) - 64
                while len(values) < column:
                    values.append("")
                raw = cell.find("m:v", namespace)
                text = "" if raw is None or raw.text is None else raw.text
                if cell.attrib.get("t") == "s" and text:
                    text = shared[int(text)]
                values[column - 1] = text
            rows.append(values)
    return rows


def load_catalog():
    rows = worksheet_rows(WORKBOOK)
    headers = [str(cell or "").strip() for cell in rows[0]]
    index = {name: position for position, name in enumerate(headers)}
    catalog = []
    for row in rows[1:]:
        if not row or len(row) <= index["key"] or not row[index["key"]]:
            continue
        catalog.append({name: row[index[name]] if index[name] < len(row) else "" for name in headers})
    return catalog


class UiTranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packs = load_packs()
        cls.catalog = load_catalog()

    def test_reviewed_keys_exist_in_every_language(self):
        for row in self.catalog:
            status = str(row.get("status") or "")
            key = str(row["key"])
            if status in SKIP_STATUS and not key.startswith("suspicion."):
                for lang in ("hr", "sr", "de"):
                    self.assertNotIn(key, self.packs[lang])
                continue
            if key.startswith("suspicion."):
                for lang, column in (("hr", "translation_hr"), ("sr", "translation_sr"), ("de", "translation_de")):
                    self.assertEqual(self.packs[lang][key], row[column], f"{lang} {key}")
                continue
            for lang in ("hr", "sr", "de"):
                self.assertIn(key, self.packs[lang], f"{lang} missing {key}")
                self.assertTrue(str(self.packs[lang][key]).strip(), f"{lang} empty {key}")

    def test_placeholders_match_source_text(self):
        for row in self.catalog:
            if str(row.get("status") or "") in SKIP_STATUS and not str(row.get("key") or "").startswith("suspicion."):
                continue
            key = str(row["key"])
            if key.startswith("suspicion."):
                expected = set(PLACEHOLDER.findall(str(row.get("translation_hr") or "")))
                for lang in ("hr", "sr", "de"):
                    self.assertEqual(expected, set(PLACEHOLDER.findall(self.packs[lang][key])), f"{lang} {key}")
                continue
            expected = set(PLACEHOLDER.findall(str(row.get("source_text") or "")))
            if key == "room.round_initial":
                continue
            for lang in ("hr", "sr", "de"):
                found = set(PLACEHOLDER.findall(self.packs[lang][key]))
                self.assertEqual(expected, found, f"{lang} {key}")

    def test_turkish_pack_contains_reviewed_translations(self):
        self.assertIn("tr", self.packs)
        for row in self.catalog:
            key = str(row["key"])
            turkish = str(row.get("translation_tr") or "").strip()
            if not turkish or key in {
                "api.room_full",
                "api.max_players",
                "rules.rule_07",
                "api.voting_not_yet",
                "rules.expanded.chapter_05.paragraph_01",
                "rules.expanded.chapter_05.prediction_intro",
                "homeScreen.title",
                "homeScreen.description",
                "homeScreen.iphone1",
                "homeScreen.android1",
                "setup.room_code_placeholder",
            }:
                continue
            self.assertEqual(self.packs["tr"][key], turkish, key)
        self.assertIn("10", self.packs["tr"]["api.max_players"])
        self.assertIn("10", self.packs["hr"]["api.room_full"])
        for key in ("rules.rule_07", "api.voting_not_yet", "rules.expanded.chapter_05.paragraph_01", "rules.expanded.chapter_05.prediction_intro"):
            for lang in ("hr", "sr", "de", "tr"):
                self.assertIn("30", self.packs[lang][key], f"{lang} {key}")
        for lang in ("hr", "sr", "de", "tr"):
            self.assertEqual(self.packs[lang]["setup.room_code_placeholder"], "1234")

    def test_stable_titles_and_chat_name(self):
        self.assertEqual(self.packs["hr"]["home.title"], "Varalica")
        self.assertEqual(self.packs["sr"]["home.title"], "Varalica")
        self.assertEqual(self.packs["de"]["home.title"], "Betrüger")
        for lang in ("hr", "sr", "de"):
            self.assertEqual(self.packs[lang]["mode.chat"], "Chat")

    def test_blocked_extend_button_keeps_source_wording(self):
        source = self.packs["source"]["results.extend_button"]
        for lang in ("hr", "sr", "de"):
            self.assertEqual(self.packs[lang]["results.extend_button"], source)

    def test_gap_strings_exist_in_every_language(self):
        keys = [
            "invite.notice",
            "chat.sent",
            "vote.select",
            "vote.cast",
            "vote.chosen",
            "vote.you",
            "vote.received",
            "vote.once",
            "discussion.phase",
            "results.host_reveal_ready",
            "spectator.wait_self",
            "spectator.wait_other",
            "room.qr_hide",
        ]
        for key in keys:
            expected = set(PLACEHOLDER.findall(self.packs["hr"][key]))
            for lang in ("hr", "sr", "de", "tr"):
                self.assertTrue(self.packs[lang][key].strip())
                self.assertEqual(expected, set(PLACEHOLDER.findall(self.packs[lang][key])))
        self.assertIn("Katıl", self.packs["tr"]["invite.notice"])
        self.assertNotEqual(self.packs["tr"]["invite.notice"], self.packs["hr"]["invite.notice"])
        self.assertNotEqual(self.packs["de"]["invite.notice"], self.packs["hr"]["invite.notice"])

    def test_dynamic_round_label_was_added(self):
        for lang, text in (
            ("hr", "Runda {round_number}"),
            ("sr", "Runda {round_number}"),
            ("de", "Runde {round_number}"),
        ):
            self.assertEqual(self.packs[lang]["room.round_label"], text)

    def test_home_screen_copy_matches_workbook(self):
        rows = [row for row in self.catalog if str(row["key"]).startswith("homeScreen.")]
        self.assertEqual(
            [row["key"] for row in rows],
            [
                "homeScreen.add",
                "homeScreen.title",
                "homeScreen.description",
                "homeScreen.iphone1",
                "homeScreen.iphone2",
                "homeScreen.iphone3",
                "homeScreen.android1",
                "homeScreen.android2",
                "homeScreen.android3",
                "homeScreen.note",
                "homeScreen.close",
            ],
        )
        columns = {
            "hr": "translation_hr",
            "sr": "translation_sr",
            "de": "translation_de",
            "tr": "translation_tr",
        }
        index = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        self.assertLess(index.index('id="setupView"'), index.index('id="homeScreenEntry"'))
        self.assertLess(index.index('id="homeScreenEntry"'), index.index('id="roomView"'))
        self.assertIn('data-i18n="homeScreen.add"', index)
        self.assertIn('data-i18n-aria="homeScreen.close"', index)
        self.assertIn('>iOS</button>', index)
        self.assertNotIn(">iPhone</button>", index)
        self.assertNotIn("beforeinstallprompt", index)
        for row in rows:
            key = str(row["key"])
            for lang, column in columns.items():
                expected = str(row[column]).strip()
                self.assertTrue(expected, f"{lang} {key} workbook value is empty")
                self.assertEqual(self.packs[lang][key], expected, f"{lang} {key}")
                self.assertNotEqual(self.packs[lang][key], key)


if __name__ == "__main__":
    unittest.main()
