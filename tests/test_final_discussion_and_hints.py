import time
import unittest
from unittest.mock import patch

from main import (
    FINAL_DISCUSSION_SECONDS,
    GAME_LANGUAGE,
    Player,
    Room,
    choose_hint_for_word,
    ensure_final_discussion_started,
    hints_for_language,
    overtime_voting_unlocked,
    private_state,
    set_host,
    voting_unlocked,
)


def discussion_room(duration: int, elapsed: float, mode: str = "live") -> Room:
    room = Room(code="TEST")
    room.state = "discussion"
    room.play_mode = mode
    room.discussion_duration_seconds = duration
    room.discussion_started_at = time.time() - elapsed
    room.host_id = "host"
    room.players["host"] = Player(id="host", name="Host", is_host=True)
    return room


class FinalDiscussionTests(unittest.TestCase):
    def setUp(self):
        self.persist = patch("main.persist_room").start()
        self.addCleanup(patch.stopall)

    def test_window_starts_after_each_configured_duration(self):
        for duration in (120, 180, 300):
            with self.subTest(duration=duration):
                before = discussion_room(duration, duration - 1)
                self.assertFalse(voting_unlocked(before))
                self.assertIsNone(before.final_discussion_started_at)

                started = discussion_room(duration, duration + 0.2)
                ensure_final_discussion_started(started)
                self.assertIsNotNone(started.final_discussion_started_at)
                self.assertAlmostEqual(
                    started.final_discussion_started_at,
                    started.discussion_started_at + duration,
                    delta=0.01,
                )
                self.assertFalse(voting_unlocked(started))

                finished = discussion_room(duration, duration + FINAL_DISCUSSION_SECONDS + 0.2)
                self.assertTrue(voting_unlocked(finished))

    def test_refresh_and_host_transfer_do_not_restart_window(self):
        room = discussion_room(120, 125)
        ensure_final_discussion_started(room)
        original = room.final_discussion_started_at
        ensure_final_discussion_started(room)
        set_host(room, "host")
        self.assertEqual(room.final_discussion_started_at, original)

    def test_live_and_chat_use_the_same_gate(self):
        for mode in ("live", "chat"):
            self.assertFalse(voting_unlocked(discussion_room(120, 80, mode)))
            self.assertFalse(voting_unlocked(discussion_room(120, 136, mode)))
            self.assertFalse(voting_unlocked(discussion_room(120, 140.2, mode)))
            self.assertTrue(voting_unlocked(discussion_room(120, 150.2, mode)))
            self.assertEqual(FINAL_DISCUSSION_SECONDS, 30)

    def test_overtime_is_independent(self):
        room = Room(code="TEST")
        room.state = "overtime"
        room.overtime_started_at = time.time()
        room.discussion_duration_seconds = 120
        self.assertTrue(overtime_voting_unlocked(room))
        self.assertIsNone(room.final_discussion_started_at)


class HintLanguageTests(unittest.TestCase):
    def test_languages_stay_separate(self):
        word = {
            "id": "kuca_001",
            "hr": "jastuk",
            "sr": "jastuk",
            "de": "Kissen",
            "hint_hr": ["odmor"],
            "hint_sr": ["spavanje"],
            "hint_de": ["Schlaf"],
            "hint_pool": ["odmor", "spavanje"],
        }
        self.assertEqual(hints_for_language(word, "hr"), ["odmor"])
        self.assertEqual(hints_for_language(word, "sr"), ["spavanje"])
        self.assertEqual(hints_for_language(word, "de"), ["Schlaf"])
        self.assertEqual(choose_hint_for_word(word, "hr"), "odmor")
        self.assertNotEqual(choose_hint_for_word(word, "hr"), "spavanje")

    def test_legacy_pool_uses_position_not_the_other_language(self):
        word = {"hr": "kruh", "sr": "hleb", "hint_pool": ["obrok", "hleb-hint"]}
        self.assertEqual(hints_for_language(word, "hr"), ["obrok"])
        self.assertEqual(hints_for_language(word, "sr"), ["hleb-hint"])
        self.assertEqual(hints_for_language(word, "de"), [])

    def test_identical_legacy_hint_is_shared_without_cross_selection(self):
        word = {"hint_pool": ["zima"]}
        self.assertEqual(hints_for_language(word, "hr"), ["zima"])
        self.assertEqual(hints_for_language(word, "sr"), ["zima"])

    def test_active_language_is_croatian_and_impostor_gets_no_word(self):
        self.assertEqual(GAME_LANGUAGE, "hr")
        room = Room(code="TEST")
        room.state = "reveal"
        room.players["impostor"] = Player(id="impostor", name="V")
        room.players["player"] = Player(id="player", name="P")
        room.round_player_ids = ["impostor", "player"]
        room.varalica_ids = ["impostor"]
        room.varalica_id = "impostor"
        room.current_word_id = "hrana_001"
        room.word = {
            "id": "hrana_001",
            "hr": "kruh",
            "sr": "hleb",
            "de": "Brot",
            "category": "Hrana",
            "hint_hr": ["obrok"],
            "hint_sr": ["jelo"],
            "hint_de": ["Essen"],
            "hint_pool": ["obrok"],
        }
        room.selected_hint = "obrok"
        room.selected_hint_index = 0
        secret = private_state(room, "impostor")
        visible = private_state(room, "player")
        self.assertNotIn("word", secret)
        self.assertNotIn("hr", secret)
        self.assertNotIn("sr", secret)
        self.assertNotIn("hint_sr", secret)
        self.assertEqual(secret["hint"], "obrok")
        self.assertEqual(visible["word"]["text"], "kruh")
        self.assertEqual(visible["word"]["id"], "hrana_001")
        self.assertNotIn("sr", visible["word"])
        self.assertNotIn("de", visible["word"])

    def test_players_share_one_concept_in_their_own_language(self):
        room = Room(code="TEST")
        room.state = "reveal"
        room.round_player_ids = ["hr", "sr", "de"]
        room.varalica_ids = ["de"]
        room.varalica_id = "de"
        room.current_word_id = "hrana_001"
        room.selected_hint = "obrok"
        room.selected_hint_index = 0
        room.word = {
            "id": "hrana_001",
            "hr": "kruh",
            "sr": "hleb",
            "de": "Brot",
            "category": "Hrana",
            "hint_hr": ["obrok"],
            "hint_sr": ["jelo"],
            "hint_de": ["Essen"],
            "hint_pool": ["obrok"],
        }
        room.players["hr"] = Player(id="hr", name="Ana", ui_language="hr")
        room.players["sr"] = Player(id="sr", name="Marko", ui_language="sr")
        room.players["de"] = Player(id="de", name="Eva", ui_language="de")
        croatian = private_state(room, "hr")
        serbian = private_state(room, "sr")
        german = private_state(room, "de")
        self.assertEqual(croatian["word"]["text"], "kruh")
        self.assertEqual(serbian["word"]["text"], "hleb")
        self.assertEqual(croatian["word"]["id"], serbian["word"]["id"])
        self.assertNotIn("word", german)
        self.assertEqual(german["hint"], "Essen")
        self.assertNotIn("kruh", german.values())
        room.players["de"].ui_language = "sr"
        self.assertEqual(private_state(room, "de")["hint"], "jelo")
        self.assertEqual(room.current_word_id, "hrana_001")

    def test_missing_german_hint_is_not_replaced(self):
        room = Room(code="TEST")
        room.state = "reveal"
        room.round_player_ids = ["de"]
        room.varalica_ids = ["de"]
        room.varalica_id = "de"
        room.current_word_id = "kuca_001"
        room.selected_hint = "odmor"
        room.selected_hint_index = 0
        room.word = {"id": "kuca_001", "hr": "zz-hr-only", "sr": "zz-sr-only", "category": "Kuća", "hint_hr": ["odmor"], "hint_pool": ["odmor"]}
        room.players["de"] = Player(id="de", name="Eva", ui_language="de")
        secret = private_state(room, "de")
        self.assertEqual(secret["hint"], "")
        self.assertNotIn("odmor", secret.values())


if __name__ == "__main__":
    unittest.main()
