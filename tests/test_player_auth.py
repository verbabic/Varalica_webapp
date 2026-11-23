import json
import time
import unittest

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import main


MUTATIONS = [
    ("/start", {"category": "Sve kategorije", "discussion_seconds": 120, "varalica_count": 1}),
    ("/view-secret", {}),
    ("/change-word", {}),
    ("/confirm", {}),
    ("/next-player", {}),
    ("/reset", {}),
    ("/play-mode", {"play_mode": "live"}),
    ("/kick", {"target_id": "someone"}),
    ("/transfer-host", {"target_id": "someone"}),
    ("/request-vote", {}),
    ("/open-final-voting", {}),
    ("/reveal", {}),
    ("/vote", {"target_id": "someone", "target_ids": ["someone"]}),
    ("/suspicion", {"target_id": "someone"}),
    ("/association", {"text": "test"}),
    ("/reaction", {"emoji": "😂", "target_type": "live_player", "target_id": "someone"}),
    ("/start-overtime", {}),
    ("/new-round", {}),
    ("/leave", {}),
    ("/tab-close", {}),
]


class PlayerAuthTests(unittest.TestCase):
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
        main.rooms.pop("LEGACY", None)
        main.persist_room = self.original_persist

    def create_player(self, name, room_code=None):
        if room_code is None:
            response = self.client.post("/api/rooms", json={"name": name, "play_mode": "live"})
        else:
            response = self.client.post(
                f"/api/rooms/{room_code}/join",
                json={"name": name, "play_mode": "live"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.codes.append(data["room_code"])
        return data

    def auth(self, credential):
        return {"Authorization": f"Bearer {credential}"}

    def test_credentials_are_unique_and_high_entropy(self):
        first = self.create_player("Ana")
        second = self.create_player("Marko")
        self.assertNotEqual(first["credential"], second["credential"])
        self.assertNotEqual(first["player_id"], first["credential"])
        self.assertGreaterEqual(len(first["credential"]), 43)
        room = main.rooms[first["room_code"]]
        verifier = room.players[first["player_id"]].credential_verifier
        self.assertEqual(len(verifier), 64)
        self.assertNotIn(first["credential"], verifier)

    def test_valid_token_and_rejections(self):
        host = self.create_player("Ana")
        room_code = host["room_code"]
        other = self.create_player("Marko", room_code)
        outsider = self.create_player("Iva")
        url = f"/api/rooms/{room_code}/play-mode"
        body = {"player_id": host["player_id"], "play_mode": "live"}

        missing = self.client.post(url, json=body)
        self.assertEqual(missing.status_code, 401)

        wrong = self.client.post(url, json=body, headers=self.auth("not-the-credential"))
        self.assertEqual(wrong.status_code, 401)

        cross = self.client.post(url, json=body, headers=self.auth(outsider["credential"]))
        self.assertEqual(cross.status_code, 401)

        impersonated = self.client.post(
            url,
            json={"player_id": other["player_id"], "play_mode": "live"},
            headers=self.auth(host["credential"]),
        )
        self.assertEqual(impersonated.status_code, 401)

        accepted = self.client.post(url, json=body, headers=self.auth(host["credential"]))
        self.assertEqual(accepted.status_code, 200)

    def test_every_mutation_rejects_a_player_id_without_a_credential(self):
        host = self.create_player("Ana")
        for path, extra in MUTATIONS:
            response = self.client.post(
                f"/api/rooms/{host['room_code']}{path}",
                json={"player_id": host["player_id"], **extra},
            )
            self.assertEqual(response.status_code, 401, path)
            self.assertNotIn(host["credential"], response.text)

    def test_host_authorization_follows_authentication(self):
        host = self.create_player("Ana")
        guest = self.create_player("Marko", host["room_code"])
        response = self.client.post(
            f"/api/rooms/{host['room_code']}/reset",
            json={"player_id": guest["player_id"]},
            headers=self.auth(guest["credential"]),
        )
        self.assertEqual(response.status_code, 403)
        transferred = self.client.post(
            f"/api/rooms/{host['room_code']}/transfer-host",
            json={"player_id": host["player_id"], "target_id": guest["player_id"]},
            headers=self.auth(host["credential"]),
        )
        self.assertEqual(transferred.status_code, 200)
        self.assertEqual(main.rooms[host["room_code"]].host_id, guest["player_id"])
        old_host = self.client.post(
            f"/api/rooms/{host['room_code']}/reset",
            json={"player_id": host["player_id"]},
            headers=self.auth(host["credential"]),
        )
        self.assertEqual(old_host.status_code, 403)

    def test_authenticated_vote_does_not_accept_another_players_id(self):
        host = self.create_player("Ana")
        players = [host]
        for name in ("Marko", "Iva", "Luka"):
            players.append(self.create_player(name, host["room_code"]))
        room = main.rooms[host["room_code"]]
        room.state = "final_voting"
        room.round_player_ids = [player["player_id"] for player in players]
        target = players[1]["player_id"]
        forged = self.client.post(
            f"/api/rooms/{host['room_code']}/vote",
            json={"player_id": target, "target_id": players[2]["player_id"], "target_ids": [players[2]["player_id"]]},
            headers=self.auth(players[0]["credential"]),
        )
        self.assertEqual(forged.status_code, 401)
        self.assertEqual(room.final_votes, {})
        voted = self.client.post(
            f"/api/rooms/{host['room_code']}/vote",
            json={"player_id": players[0]["player_id"], "target_id": target, "target_ids": [target]},
            headers=self.auth(players[0]["credential"]),
        )
        self.assertEqual(voted.status_code, 200)
        self.assertEqual(room.final_votes[players[0]["player_id"]], [target])

    def test_snapshot_restores_verifier_without_exposing_credential(self):
        host = self.create_player("Ana")
        room = main.rooms[host["room_code"]]
        snapshot = main.room_to_snapshot(room)
        encoded = json.dumps(snapshot)
        self.assertNotIn(host["credential"], encoded)
        self.assertIn(room.players[host["player_id"]].credential_verifier, encoded)
        main.rooms.pop(host["room_code"])
        restored = main.room_from_snapshot(snapshot)
        main.rooms[restored.code] = restored
        public = json.dumps(main.public_state(restored, host["player_id"]))
        self.assertNotIn(host["credential"], public)
        self.assertNotIn("credential_verifier", public)
        response = self.client.post(
            f"/api/rooms/{restored.code}/play-mode",
            json={"player_id": host["player_id"], "play_mode": "live"},
            headers=self.auth(host["credential"]),
        )
        self.assertEqual(response.status_code, 200)

    def test_legacy_room_is_rejected(self):
        room = main.room_from_snapshot({"code": "LEGACY", "players": [{"id": "old-player", "name": "Ana"}]})
        main.rooms["LEGACY"] = room
        self.assertTrue(room.legacy_unauthenticated)
        response = self.client.post(
            "/api/rooms/LEGACY/leave",
            json={"player_id": "old-player"},
            headers=self.auth("legacy-secret"),
        )
        self.assertEqual(response.status_code, 403)
        joined = self.client.post("/api/rooms/LEGACY/join", json={"name": "Nova"})
        self.assertEqual(joined.status_code, 403)

    def test_name_or_player_id_cannot_reclaim_a_seat(self):
        host = self.create_player("Ana")
        stolen = self.client.post(
            f"/api/rooms/{host['room_code']}/join",
            json={"name": "Ana", "player_id": host["player_id"]},
        )
        self.assertEqual(stolen.status_code, 400)
        self.assertEqual(len(main.rooms[host["room_code"]].players), 1)
        reclaimed = self.client.post(
            f"/api/rooms/{host['room_code']}/join",
            json={"name": "Ana Nova", "player_id": host["player_id"]},
            headers=self.auth(host["credential"]),
        )
        self.assertEqual(reclaimed.status_code, 200)
        self.assertEqual(reclaimed.json()["player_id"], host["player_id"])
        self.assertNotIn("credential", reclaimed.json())

    def test_removed_player_credential_cannot_return(self):
        host = self.create_player("Ana")
        guest = self.create_player("Marko", host["room_code"])
        left = self.client.post(
            f"/api/rooms/{host['room_code']}/leave",
            json={"player_id": guest["player_id"]},
            headers=self.auth(guest["credential"]),
        )
        self.assertEqual(left.status_code, 200)
        self.assertNotIn(guest["player_id"], main.rooms[host["room_code"]].players)
        returned = self.client.post(
            f"/api/rooms/{host['room_code']}/join",
            json={"name": "Marko", "player_id": guest["player_id"]},
            headers=self.auth(guest["credential"]),
        )
        self.assertEqual(returned.status_code, 401)

    def test_websocket_sends_state_only_after_authentication(self):
        host = self.create_player("Ana")
        url = f"/ws/{host['room_code']}/{host['player_id']}"
        with self.client.websocket_connect(url) as socket:
            socket.send_json({"type": "auth", "credential": "wrong"})
            with self.assertRaises(WebSocketDisconnect):
                socket.receive_json()
        with self.client.websocket_connect(url) as socket:
            socket.send_json({"type": "auth", "credential": host["credential"]})
            state = socket.receive_json()
        self.assertEqual(state["room_code"], host["room_code"])
        self.assertNotIn(host["credential"], json.dumps(state))
        self.assertNotIn("credential_verifier", json.dumps(state))

    def test_websocket_auth_timeout_and_oversized_message(self):
        host = self.create_player("Ana")
        url = f"/ws/{host['room_code']}/{host['player_id']}"
        original_timeout = main.WS_AUTH_TIMEOUT_SECONDS
        main.WS_AUTH_TIMEOUT_SECONDS = 0.2
        try:
            started = time.monotonic()
            with self.client.websocket_connect(url) as socket:
                with self.assertRaises(WebSocketDisconnect):
                    socket.receive_json()
            self.assertLess(time.monotonic() - started, 2)
            with self.client.websocket_connect(url) as socket:
                socket.send_text("x" * (main.WS_AUTH_MESSAGE_BYTES + 50))
                with self.assertRaises(WebSocketDisconnect):
                    socket.receive_json()
        finally:
            main.WS_AUTH_TIMEOUT_SECONDS = original_timeout
        self.assertTrue(main.rooms[host["room_code"]].players[host["player_id"]].credential_verifier)

    def test_second_socket_does_not_drop_the_player_when_the_first_closes(self):
        host = self.create_player("Ana")
        url = f"/ws/{host['room_code']}/{host['player_id']}"
        with self.client.websocket_connect(url) as first:
            first.send_json({"type": "auth", "credential": host["credential"]})
            first.receive_json()
            with self.client.websocket_connect(url) as second:
                second.send_json({"type": "auth", "credential": host["credential"]})
                second.receive_json()
                room = main.rooms[host["room_code"]]
                current = room.sockets[host["player_id"]]
                first.close()
                self.assertIs(room.sockets[host["player_id"]], current)
                self.assertTrue(room.players[host["player_id"]].connected)


if __name__ == "__main__":
    unittest.main()
