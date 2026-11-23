import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import main
import storage


class HealthEndpointTests(unittest.TestCase):
    def setUp(self):
        self.original_db = storage.DB_PATH
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        storage.DB_PATH = Path(self.tmp.name) / "health.sqlite3"
        self.client = TestClient(main.app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.original_db
        self.tmp.cleanup()

    def test_health_matches_monitor_contract(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(response.content, b'{"ok":true}')
        self.assertNotIn(b"sqlite", response.content.lower())
        self.assertNotIn(b"varalica_db", response.content.lower())
