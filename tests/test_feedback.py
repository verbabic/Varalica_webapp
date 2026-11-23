import json
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import main
import storage


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
I18N = (ROOT / "static" / "i18n.js").read_text(encoding="utf-8")


def load_packs():
    match = re.search(r"const UI_PACKS = (\{.*?\});\nconst ", I18N, re.S)
    if not match:
        raise AssertionError("UI_PACKS block was not found")
    return json.loads(match.group(1))


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.original_db = storage.DB_PATH
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        storage.DB_PATH = Path(self.tmp.name) / "feedback.sqlite3"
        main._feedback_hits.clear()
        self.client = TestClient(main.app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.original_db
        main._feedback_hits.clear()
        self.tmp.cleanup()

    def post_feedback(self, **overrides):
        payload = {
            "category": "bug",
            "message": "The timer froze after voting.",
            "email": None,
            "ui_language": "hr",
        }
        payload.update(overrides)
        return self.client.post("/api/feedback", json=payload)

    def rows(self):
        with sqlite3.connect(storage.DB_PATH) as connection:
            return connection.execute(
                "SELECT id, category, message, email, ui_language, created_at FROM feedback ORDER BY id"
            ).fetchall()

    def test_button_labels_and_modal_copy(self):
        from tests.test_ui_translations import load_catalog

        packs = load_packs()
        self.assertLess(INDEX.index('id="rulesButton"'), INDEX.index('id="contactButton"'))
        self.assertIn('class="header-utility-actions"', INDEX)
        self.assertIn('aria-labelledby="contactTitle"', INDEX)
        self.assertIn('class="contact-close"', INDEX)
        self.assertNotIn('id="contactCancelButton"', INDEX)
        self.assertIn('id="contactModal"', INDEX)
        self.assertIn("M21 15a2 2 0 0 1-2 2H7l-4 4V5", INDEX)
        rows = [row for row in load_catalog() if str(row["key"]).startswith("contact.")]
        self.assertEqual(len(rows), 23)
        columns = {
            "hr": "translation_hr",
            "sr": "translation_sr",
            "de": "translation_de",
            "tr": "translation_tr",
        }
        for row in rows:
            key = str(row["key"])
            for lang, column in columns.items():
                self.assertEqual(packs[lang][key], row[column], f"{lang} {key}")
                self.assertFalse(packs[lang][key].startswith("contact."), key)
            self.assertNotIn(key, packs["hr"].get("feedback.open", ""))
        self.assertEqual(packs["sr"]["contact.open_button"], "Kontakt")
        self.assertEqual(packs["hr"]["contact.open_button"], "Kontakt")
        self.assertEqual(packs["de"]["contact.open_button"], "Kontakt")
        self.assertEqual(packs["tr"]["contact.open_button"], "İletişim")
        privacy = next(row for row in rows if row["key"] == "contact.privacy")
        self.assertEqual(privacy["status"], "NEEDS_LEGAL_REVIEW")
        for lang in columns:
            self.assertNotIn("GDPR", packs[lang]["contact.privacy"])
        for obsolete in (
            "contact.placeholder.bug",
            "contact.error.generic",
            "contact.error.too_short",
        ):
            self.assertNotIn(obsolete, packs["hr"])

    def test_message_and_email_validation(self):
        short = self.post_feedback(message="abcd")
        self.assertEqual(short.status_code, 400)
        self.assertEqual(short.json()["detail"], "message_too_short")
        spaced = self.post_feedback(message="  ab  ")
        self.assertEqual(spaced.status_code, 400)
        self.assertEqual(spaced.json()["detail"], "message_too_short")
        blank = self.post_feedback(message="          ")
        self.assertEqual(blank.status_code, 400)
        self.assertEqual(blank.json()["detail"], "message_too_short")
        missing = self.post_feedback(category="nope")
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(missing.json()["detail"], "category_required")
        long = self.post_feedback(message="x" * 2001)
        self.assertEqual(long.status_code, 400)
        self.assertEqual(long.json()["detail"], "message_too_long")
        email = self.post_feedback(email="not-an-email")
        self.assertEqual(email.status_code, 400)
        self.assertEqual(email.json()["detail"], "email_invalid")
        self.assertEqual(self.rows(), [])

    def test_five_trimmed_characters_are_accepted(self):
        response = self.post_feedback(message="  abcde  ")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.rows()[0][2], "abcde")
        spaced = self.post_feedback(message="ab cd", category="other")
        self.assertEqual(spaced.status_code, 200, spaced.text)
        self.assertEqual(self.rows()[1][2], "ab cd")

    def test_successful_persistence_stores_text_not_html(self):
        message = "<script>alert(1)</script> expected a score"
        response = self.post_feedback(message=message, email="Player@Example.com", ui_language="sr", category="improvement")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(set(body), {"ok", "id"})
        self.assertTrue(body["ok"])
        self.assertNotIn(message, response.text)
        self.assertNotIn("player@example.com", response.text)
        stored = self.rows()
        self.assertEqual(len(stored), 1)
        feedback_id, category, stored_message, email, language, created_at = stored[0]
        self.assertEqual(feedback_id, body["id"])
        self.assertEqual(category, "improvement")
        self.assertEqual(stored_message, message)
        self.assertEqual(email, "player@example.com")
        self.assertEqual(language, "sr")
        self.assertRegex(created_at, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

    def test_store_failure_is_generic_and_not_success(self):
        def fail(*_args, **_kwargs):
            raise sqlite3.OperationalError("sensitive message should stay private")

        original = main.insert_feedback
        main.insert_feedback = fail
        try:
            response = self.post_feedback()
        finally:
            main.insert_feedback = original
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "feedback_failed"})
        self.assertNotIn("ok", response.json())
        self.assertNotIn("sensitive", response.text)
        self.assertNotIn("The timer froze", response.text)
        self.assertEqual(self.rows(), [])

    def test_duplicate_returns_existing_success_without_second_row(self):
        payload = {
            "category": "other",
            "message": "Same note about the lobby.",
            "email": "friend@example.com",
            "ui_language": "de",
        }
        first = self.client.post("/api/feedback", json=payload)
        second = self.client.post("/api/feedback", json=payload)
        self.assertEqual(first.status_code, 200)
        self.assertNotIn("duplicate", first.json())
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()["duplicate"])
        self.assertEqual(first.json()["id"], second.json()["id"])
        self.assertEqual(len(self.rows()), 1)
        with sqlite3.connect(storage.DB_PATH) as connection:
            connection.execute(
                "UPDATE feedback SET created_at = ? WHERE id = ?",
                ("2000-01-01 00:00:00", first.json()["id"]),
            )
        third = self.client.post("/api/feedback", json=payload)
        self.assertEqual(third.status_code, 200)
        self.assertNotEqual(third.json()["id"], first.json()["id"])
        self.assertEqual(len(self.rows()), 2)

    def test_rate_limit_blocks_new_messages_only(self):
        ids = []
        for index in range(main.FEEDBACK_RATE_LIMIT_COUNT):
            response = self.post_feedback(message=f"Distinct report number {index} ok")
            self.assertEqual(response.status_code, 200, response.text)
            ids.append(response.json()["id"])
        blocked = self.post_feedback(message="Another distinct report after the limit")
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.json()["detail"], "rate_limited")
        self.assertNotIn("ok", blocked.json())
        self.assertEqual(len(self.rows()), main.FEEDBACK_RATE_LIMIT_COUNT)
        retry = self.post_feedback(message="Distinct report number 0 ok")
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.json()["id"], ids[0])
        self.assertEqual(len(self.rows()), main.FEEDBACK_RATE_LIMIT_COUNT)

    def test_oversized_request_is_rejected(self):
        response = self.client.post(
            "/api/feedback",
            content=b'{"category":"bug","message":"' + (b"x" * 17000) + b'"}',
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["detail"], "feedback_rejected")
        self.assertEqual(self.rows(), [])

    def test_feedback_has_no_public_read(self):
        created = self.post_feedback(message="Private feedback text for listing check")
        self.assertEqual(created.status_code, 200)
        feedback_id = created.json()["id"]
        for path in ("/api/feedback", f"/api/feedback/{feedback_id}"):
            response = self.client.get(path)
            self.assertIn(response.status_code, (404, 405))
            self.assertNotIn("Private feedback text", response.text)
        with sqlite3.connect(storage.DB_PATH) as connection:
            connection.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
            remaining = connection.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        self.assertEqual(remaining, 0)

    def test_gameplay_constant_unchanged(self):
        self.assertEqual(main.FINAL_DISCUSSION_SECONDS, 30)


if __name__ == "__main__":
    unittest.main()
