import hashlib
import tempfile
import unittest
from pathlib import Path

import storage
from main import Room, choose_word, hints_for_language, word_text_for_language
from scripts.import_words_from_xlsx import (
    CatalogSyncError,
    concept_pair,
    load_approved_concepts,
    synchronize_catalog,
)
from storage import init_storage, load_used_word_indexes, save_used_word_index
from words import STARTER_WORDS, is_active_word, words_for_category


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "Database words HR SR.xlsx"
PRESERVED_ID_HASH = "c301d17c0aca2a0d6973cee6aba2ebd0f8786e20de5e2b60a841b0aa0c07c417"
REPO_DB = ROOT / "varalica.sqlite3"


def approved_concepts():
    _sheet_name, concepts = load_approved_concepts(SOURCE)
    return concepts


class CatalogSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.concepts = approved_concepts()
        cls.active = [word for word in STARTER_WORDS if is_active_word(word)]
        cls.inactive = [word for word in STARTER_WORDS if not is_active_word(word)]

    def test_counts_match_the_cleaned_workbook(self):
        self.assertEqual(len(self.concepts), 1169)
        self.assertEqual(len(STARTER_WORDS), 1231)
        self.assertEqual(len(self.active), 1169)
        self.assertEqual(len(self.inactive), 62)

    def test_original_indexes_and_ids_stay_in_place(self):
        preserved = [word["id"] for word in STARTER_WORDS[:1014]]
        digest = hashlib.sha256("\n".join(preserved).encode()).hexdigest()
        self.assertEqual(digest, PRESERVED_ID_HASH)
        self.assertEqual(STARTER_WORDS[0]["id"], "hrana_001")
        self.assertEqual(STARTER_WORDS[10]["id"], "posao_002")
        self.assertEqual(STARTER_WORDS[41]["id"], "hrana_006")
        self.assertEqual(STARTER_WORDS[822]["id"], "kuca_064")
        self.assertEqual(STARTER_WORDS[1013]["id"], "zivotinje_078")
        self.assertEqual(len({word["id"] for word in STARTER_WORDS}), len(STARTER_WORDS))

    def test_every_active_concept_matches_its_workbook_row(self):
        by_pair = {concept["pair"]: concept for concept in self.concepts}
        seen = set()
        for word in self.active:
            pair = concept_pair(word["hr"], word["sr"])
            self.assertNotIn(pair, seen)
            seen.add(pair)
            source = by_pair[pair]
            self.assertEqual(word["hr"], source["hr"])
            self.assertEqual(word["sr"], source["sr"])
            self.assertEqual(word["de"], source["de"])
            self.assertEqual(word["tr"], source["tr"])
            self.assertEqual(word["category"], source["category"])
            self.assertEqual(word["hint_hr"], source["hint_hr"])
            self.assertEqual(word["hint_sr"], source["hint_sr"])
            self.assertEqual(word["hint_de"], source["hint_de"])
            self.assertEqual(word["hint_tr"], source["hint_tr"])
            self.assertEqual(word["hint_pool"], source["hint_hr"])
            for field in ("hr", "sr", "de", "tr"):
                self.assertTrue(str(word[field]).strip())
            for field in ("hint_hr", "hint_sr", "hint_de", "hint_tr"):
                self.assertTrue(word[field])
                self.assertTrue(all(str(hint).strip() for hint in word[field]))
        self.assertEqual(seen, set(by_pair))

    def test_serbian_hint_is_not_replaced_by_croatian(self):
        word = STARTER_WORDS[10]
        self.assertEqual(word["id"], "posao_002")
        self.assertEqual(hints_for_language(word, "hr"), ["ured"])
        self.assertEqual(hints_for_language(word, "sr"), ["kancelarija"])
        self.assertEqual(hints_for_language(word, "de"), ["Büro"])
        self.assertEqual(hints_for_language(word, "tr"), ["Ofis"])
        self.assertEqual(word_text_for_language(word, "hr"), "sastanak")
        self.assertEqual(word_text_for_language(word, "sr"), "sastanak")
        self.assertEqual(word_text_for_language(word, "de"), "Besprechung")
        self.assertEqual(word_text_for_language(word, "tr"), "Toplantı")
        self.assertEqual(word_text_for_language({"hr": "kruh", "sr": ""}, "sr"), "")

    def test_kuca_064_uses_the_workbook_spelling(self):
        word = STARTER_WORDS[822]
        self.assertEqual(word["hr"], "slavina")
        self.assertNotIn("\u0430", word["hr"])
        self.assertEqual(word["hint_hr"], ["kupaonica"])
        self.assertEqual(word["hint_sr"], ["kupatilo"])
        self.assertEqual(word["tr"], "Musluk")

    def test_turkish_characters_survive(self):
        text = " ".join(word["tr"] for word in self.active)
        for character in "ışğüşöçİŞÜÖÇ":
            self.assertIn(character, text)

    def test_inactive_words_cannot_be_selected(self):
        selectable = words_for_category("Sve kategorije")
        self.assertEqual(len(selectable), 1169)
        self.assertTrue(all(is_active_word(word) for word in selectable))
        self.assertNotIn("hrana_006", {word["id"] for word in selectable})
        self.assertFalse(STARTER_WORDS[41]["active"])
        self.assertEqual(STARTER_WORDS[41]["hr"], "juha")

    def test_repeated_import_does_not_change_the_catalog(self):
        repeated, report = synchronize_catalog(list(STARTER_WORDS), self.concepts)
        self.assertEqual(repeated, list(STARTER_WORDS))
        self.assertEqual(report["appended"], 0)
        self.assertEqual(report["physical"], 1231)
        self.assertEqual(report["active"], 1169)
        self.assertEqual(report["inactive"], 62)

    def test_duplicate_concepts_are_rejected(self):
        first = {
            "pair": ("kruh", "hleb"),
            "category": "Hrana",
            "hr": "kruh",
            "sr": "hleb",
            "de": "Brot",
            "tr": "Ekmek",
            "hint_hr": ["obrok"],
            "hint_sr": ["jelo"],
            "hint_de": ["Essen"],
            "hint_tr": ["yemek"],
        }
        with self.assertRaises(CatalogSyncError):
            synchronize_catalog([], [first, dict(first)])

    def test_missing_concepts_are_deactivated_and_new_ones_are_appended(self):
        starter = [
            {
                "id": "hrana_001",
                "hr": "kruh",
                "sr": "hleb",
                "category": "Hrana",
                "difficulty": "normal",
                "hint_pool": ["obrok"],
            },
            {
                "id": "hrana_002",
                "hr": "stara",
                "sr": "rec",
                "category": "Hrana",
                "difficulty": "easy",
                "hint_pool": ["stara"],
            },
        ]
        concepts = [
            {
                "pair": concept_pair("kruh", "hleb"),
                "category": "Hrana",
                "hr": "kruh",
                "sr": "hleb",
                "de": "Brot",
                "tr": "Ekmek",
                "hint_hr": ["obrok"],
                "hint_sr": ["jelo"],
                "hint_de": ["Essen"],
                "hint_tr": ["yemek"],
            },
            {
                "pair": concept_pair("nova", "rec"),
                "category": "Hrana",
                "hr": "nova",
                "sr": "rec",
                "de": "Neu",
                "tr": "Yeni",
                "hint_hr": ["hr"],
                "hint_sr": ["sr"],
                "hint_de": ["de"],
                "hint_tr": ["tr"],
            },
        ]
        catalog, report = synchronize_catalog(starter, concepts)
        self.assertEqual([word["id"] for word in catalog[:2]], ["hrana_001", "hrana_002"])
        self.assertTrue(catalog[0]["active"])
        self.assertEqual(catalog[0]["hint_sr"], ["jelo"])
        self.assertFalse(catalog[1]["active"])
        self.assertEqual(catalog[1]["hr"], "stara")
        self.assertEqual(catalog[2]["id"], "hrana_003")
        self.assertTrue(catalog[2]["active"])
        self.assertEqual(report["appended"], 1)
        self.assertEqual(report["inactive_absent"], 1)
        again, _report = synchronize_catalog(catalog, concepts)
        self.assertEqual(again, catalog)


class CatalogSelectionTests(unittest.TestCase):
    def setUp(self):
        self.original_db = storage.DB_PATH
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        storage.DB_PATH = Path(self.tmp.name) / "catalog.sqlite3"
        self.assertNotEqual(storage.DB_PATH.resolve(), REPO_DB.resolve())
        init_storage()

    def tearDown(self):
        storage.DB_PATH = self.original_db
        self.tmp.cleanup()

    def test_new_draw_skips_inactive_slots(self):
        inactive_ids = {word["id"] for word in STARTER_WORDS if not is_active_word(word)}
        room = Room(code="DRAW1")
        for _ in range(25):
            chosen = choose_word(room)
            self.assertTrue(chosen.get("active", True))
            self.assertNotIn(chosen["id"], inactive_ids)
            self.assertTrue(chosen.get("hint_sr"))
            self.assertTrue(chosen.get("hint_tr"))

    def test_inactive_history_survives_a_full_active_reset(self):
        inactive_index = 41
        self.assertFalse(STARTER_WORDS[inactive_index]["active"])
        active_indexes = [index for index, word in enumerate(STARTER_WORDS) if is_active_word(word)]
        for index in active_indexes:
            save_used_word_index("HIST1", index)
        save_used_word_index("HIST1", inactive_index)

        chosen = choose_word(Room(code="HIST1"))
        stored = load_used_word_indexes("HIST1")

        self.assertTrue(chosen.get("active", True))
        self.assertIn(inactive_index, stored)
        self.assertEqual(STARTER_WORDS[inactive_index]["id"], "hrana_006")
        self.assertNotIn("hrana_006", {chosen["id"]})
        self.assertEqual(len(stored), 2)


if __name__ == "__main__":
    unittest.main()
