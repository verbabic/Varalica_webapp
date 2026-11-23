import tempfile
import threading
import unittest
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient

import main
import storage


class RoomCodeTests(unittest.TestCase):
    def setUp(self):
        self.original_db = storage.DB_PATH
        self.original_rooms = dict(main.rooms)
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        storage.DB_PATH = Path(self.tmp.name) / "rooms.sqlite3"
        main.rooms.clear()
        self.client = TestClient(main.app)
        self.client.__enter__()
        self.created = []

    def tearDown(self):
        self.client.__exit__(None, None, None)
        main.rooms.clear()
        main.rooms.update(self.original_rooms)
        storage.DB_PATH = self.original_db
        self.tmp.cleanup()

    def test_new_codes_have_four_digits_and_do_not_collide(self):
        codes = set()
        for index in range(30):
            response = self.client.post("/api/rooms", json={"name": f"Ana{index:02d}"})
            self.assertEqual(response.status_code, 200, response.text)
            code = response.json()["room_code"]
            self.created.append(code)
            self.assertRegex(code, r"^[1-9][0-9]{3}$")
            self.assertNotIn(code, codes)
            codes.add(code)
        self.assertEqual(len(codes), 30)

    def test_existing_five_digit_room_still_joins_and_link_route_works(self):
        storage.save_room_snapshot("54321", {"code": "54321", "state": "lobby", "players": [], "host_id": None})
        main.load_persisted_rooms()
        self.assertIn("54321", main.rooms)

        created = self.client.post("/api/rooms", json={"name": "Ana"}).json()
        self.created.append(created["room_code"])
        self.assertRegex(created["room_code"], r"^[1-9][0-9]{3}$")
        self.assertNotEqual(created["room_code"], "54321")

        page = self.client.get("/room/54321")
        self.assertEqual(page.status_code, 200)
        self.assertIn('id="roomCode"', page.text)
        four_digit_page = self.client.get(f"/room/{created['room_code']}")
        self.assertEqual(four_digit_page.status_code, 200)
        self.assertIn('maxlength="4"', four_digit_page.text)

        original = main.make_room_code
        main.make_room_code = lambda: "12345"
        try:
            legacy = self.client.post("/api/rooms", json={"name": "Iva"})
        finally:
            main.make_room_code = original
        self.assertEqual(legacy.status_code, 200)
        self.assertEqual(legacy.json()["room_code"], "12345")
        joined = self.client.post("/api/rooms/12345/join", json={"name": "Marko"})
        self.assertEqual(joined.status_code, 200)
        self.assertEqual(joined.json()["room_code"], "12345")
        self.assertEqual(self.client.get("/api/rooms/12345/status").status_code, 200)

    def test_collision_skips_active_and_recoverable_codes(self):
        main.rooms["4321"] = object()
        storage.save_room_snapshot("2468", {"code": "2468"})
        main.rooms.pop("2468", None)
        original_randint = main.random.randint
        original_choice = main.random.choice
        attempts = {"count": 0}

        def counting_randint(start, end):
            self.assertEqual((start, end), (1000, 9999))
            attempts["count"] += 1
            return 4321 if attempts["count"] <= 64 else 2468

        main.random.randint = counting_randint
        main.random.choice = lambda values: values[0]
        try:
            code = main.make_room_code()
        finally:
            main.random.randint = original_randint
            main.random.choice = original_choice
        self.assertRegex(code, r"^[1-9][0-9]{3}$")
        self.assertNotIn(code, {"4321", "2468"})

    def test_creation_fails_when_every_four_digit_code_is_taken(self):
        for value in range(1000, 10000):
            main.rooms[f"{value:04d}"] = object()
        with self.assertRaises(HTTPException) as raised:
            main.make_room_code()
        self.assertEqual(raised.exception.status_code, 503)
        response = self.client.post("/api/rooms", json={"name": "Ana"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Nema slobodnog koda sobe.")

    def test_concurrent_creation_does_not_duplicate_codes(self):
        codes = []
        errors = []

        def allocate():
            try:
                with main._room_code_lock:
                    code = main.make_room_code()
                    self.assertNotIn(code, main.rooms)
                    main.rooms[code] = object()
                    codes.append(code)
            except Exception as error:
                errors.append(error)

        threads = [threading.Thread(target=allocate) for _ in range(40)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 4 for code in codes))
