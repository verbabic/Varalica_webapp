import unittest

from fastapi.testclient import TestClient

import main


class PlayerLimitTests(unittest.TestCase):
    def setUp(self):
        self.original_persist = main.persist_room
        main.persist_room = lambda room: None
        self.client = TestClient(main.app)
        self.client.__enter__()
        self.codes = []

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for code in self.codes:
            main.rooms.pop(code, None)
        main.persist_room = self.original_persist

    def join(self, code, name):
        response = self.client.post(f"/api/rooms/{code}/join", json={"name": name, "play_mode": "live"})
        return response

    def test_limits_and_two_impostors(self):
        self.assertEqual(main.MIN_PLAYERS, 4)
        self.assertEqual(main.MAX_PLAYERS, 10)
        self.assertEqual(main.normalize_varalica_count(2, 6), 1)
        self.assertEqual(main.normalize_varalica_count(2, 7), 2)
        self.assertEqual(main.FINAL_DISCUSSION_SECONDS, 30)
        self.assertEqual(main.OVERTIME_SECONDS, 30)

        created = self.client.post("/api/rooms", json={"name": "Ana", "play_mode": "live"})
        self.assertEqual(created.status_code, 200, created.text)
        host = created.json()
        code = host["room_code"]
        self.codes.append(code)
        for name in ["Marko", "Iva", "Eva", "Luka", "Nika", "Petar", "Mia", "Ivan", "Ena"]:
            response = self.join(code, name)
            self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(main.rooms[code].players), 10)
        eleventh = self.join(code, "Extra")
        self.assertEqual(eleventh.status_code, 400, eleventh.text)
        started = self.client.post(
            f"/api/rooms/{code}/start",
            json={"player_id": host["player_id"], "category": "Sve kategorije", "discussion_seconds": 120, "varalica_count": 2},
            headers={"Authorization": f"Bearer {host['credential']}"},
        )
        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(len(main.rooms[code].varalica_ids), 2)

        small = self.client.post("/api/rooms", json={"name": "Ana", "play_mode": "live"})
        small_host = small.json()
        small_code = small_host["room_code"]
        self.codes.append(small_code)
        self.join(small_code, "Marko")
        self.join(small_code, "Iva")
        too_small = self.client.post(
            f"/api/rooms/{small_code}/start",
            json={"player_id": small_host["player_id"], "category": "Sve kategorije", "discussion_seconds": 120, "varalica_count": 1},
            headers={"Authorization": f"Bearer {small_host['credential']}"},
        )
        self.assertEqual(too_small.status_code, 400, too_small.text)
        self.assertIn("4", too_small.json()["detail"])


if __name__ == "__main__":
    unittest.main()
