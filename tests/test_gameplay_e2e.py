import asyncio
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import main
import storage


LANGUAGES = ("hr", "sr", "de", "tr")


class MultiplayerGameplayTests(unittest.TestCase):
    def setUp(self):
        self.original_db = storage.DB_PATH
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        storage.DB_PATH = Path(self.tmp.name) / "gameplay.sqlite3"
        main.rooms.clear()
        self.client = TestClient(main.app)
        self.client.__enter__()

    def tearDown(self):
        for room in list(main.rooms.values()):
            main.stop_timer(room)
            if room.empty_cleanup_task and not room.empty_cleanup_task.done():
                room.empty_cleanup_task.cancel()
        main.rooms.clear()
        self.client.__exit__(None, None, None)
        storage.DB_PATH = self.original_db
        self.tmp.cleanup()

    @staticmethod
    def auth(player):
        return {"Authorization": f"Bearer {player['credential']}"}

    def create_group(self, count, languages=LANGUAGES, mode="live"):
        players = []
        for index in range(count):
            language = languages[index % len(languages)]
            payload = {
                "name": f"Player {index + 1}",
                "play_mode": mode,
                "ui_language": language,
            }
            if not players:
                response = self.client.post("/api/rooms", json=payload)
            else:
                response = self.client.post(
                    f"/api/rooms/{players[0]['room_code']}/join",
                    json=payload,
                )
            self.assertEqual(response.status_code, 200, response.text)
            data = response.json()
            data["language"] = language
            players.append(data)
        return players

    def start_round(self, players, varalica_count=1):
        host = players[0]
        with patch("main.secrets.choice", side_effect=lambda items: list(items)[0]):
            response = self.client.post(
                f"/api/rooms/{host['room_code']}/start",
                json={
                    "player_id": host["player_id"],
                    "category": "Sve kategorije",
                    "discussion_seconds": 120,
                    "varalica_count": varalica_count,
                },
                headers=self.auth(host),
            )
        self.assertEqual(response.status_code, 200, response.text)
        return main.rooms[host["room_code"]]

    def confirm_all(self, players):
        for player in players:
            response = self.client.post(
                f"/api/rooms/{player['room_code']}/confirm",
                json={"player_id": player["player_id"]},
                headers=self.auth(player),
            )
            self.assertEqual(response.status_code, 200, response.text)
        room = main.rooms[players[0]["room_code"]]
        self.assertEqual(room.state, "discussion")
        main.stop_timer(room)
        return room

    def open_voting(self, players):
        room = main.rooms[players[0]["room_code"]]
        room.discussion_started_at = time.time() - room.discussion_duration_seconds - main.FINAL_DISCUSSION_SECONDS - 1
        room.final_discussion_started_at = room.discussion_started_at + room.discussion_duration_seconds
        response = self.client.post(
            f"/api/rooms/{room.code}/open-final-voting",
            json={"player_id": players[0]["player_id"]},
            headers=self.auth(players[0]),
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(room.state, "final_voting")
        return room

    def vote(self, player, target_ids):
        return self.client.post(
            f"/api/rooms/{player['room_code']}/vote",
            json={
                "player_id": player["player_id"],
                "target_id": target_ids[0],
                "target_ids": target_ids,
            },
            headers=self.auth(player),
        )

    def test_full_four_language_round_scoring_new_round_and_reset(self):
        players = self.create_group(4)
        room = self.start_round(players)
        first_word_id = room.current_word_id
        first_varalica_ids = list(room.varalica_ids)
        self.assertEqual(len(first_varalica_ids), 1)

        for player in players:
            player_id = player["player_id"]
            private = main.private_state(room, player_id)
            self.assertEqual(private["language"] if private["role"] == "varalica" else private["word"]["language"], player["language"])
            if player_id in first_varalica_ids:
                self.assertNotIn("word", private)
                self.assertEqual(
                    private["hint"],
                    main.hint_text_for_language(room.word, player["language"], room.selected_hint_index),
                )
            else:
                self.assertEqual(
                    private["word"]["text"],
                    main.word_text_for_language(room.word, player["language"]),
                )
                self.assertEqual(private["word"]["id"], first_word_id)

        self.confirm_all(players)
        self.open_voting(players)
        impostor_id = first_varalica_ids[0]
        fallback = next(player["player_id"] for player in players if player["player_id"] != impostor_id)
        for player in players:
            target = fallback if player["player_id"] == impostor_id else impostor_id
            response = self.vote(player, [target])
            self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(room.state, "voting_complete")

        reveal = self.client.post(
            f"/api/rooms/{room.code}/reveal",
            json={"player_id": players[0]["player_id"]},
            headers=self.auth(players[0]),
        )
        self.assertEqual(reveal.status_code, 200, reveal.text)
        self.assertEqual(room.state, "results")
        self.assertTrue(main.results_state(room, players[0]["player_id"])["was_varalica_caught"])
        for player in players:
            score = room.scoreboard[player["player_id"]]
            if player["player_id"] == impostor_id:
                self.assertEqual(score, {"discoveries": 0, "survivals": 0})
            else:
                self.assertEqual(score["discoveries"], 1)

        next_round = self.client.post(
            f"/api/rooms/{room.code}/new-round",
            json={"player_id": players[0]["player_id"]},
            headers=self.auth(players[0]),
        )
        self.assertEqual(next_round.status_code, 200, next_round.text)
        self.assertEqual(room.round_number, 2)
        self.assertNotEqual(room.current_word_id, first_word_id)
        self.assertNotEqual(room.varalica_ids, first_varalica_ids)
        self.assertIn(room.current_word_id, {word["id"] for word in main.STARTER_WORDS if word.get("active", True)})

        reset = self.client.post(
            f"/api/rooms/{room.code}/reset",
            json={"player_id": players[0]["player_id"]},
            headers=self.auth(players[0]),
        )
        self.assertEqual(reset.status_code, 200, reset.text)
        self.assertEqual(room.state, "lobby")
        self.assertEqual(room.round_number, 1)
        self.assertIsNone(room.word)
        self.assertTrue(all(stats == {"discoveries": 0, "survivals": 0} for stats in room.scoreboard.values()))
        self.assertEqual(storage.load_used_word_indexes(room.code), room.used_word_indexes)

    def test_two_varalice_require_two_targets_and_score_correctly(self):
        players = self.create_group(7)
        room = self.start_round(players, varalica_count=2)
        self.assertEqual(len(room.varalica_ids), 2)
        self.assertEqual(main.required_vote_target_count(room), 2)
        self.confirm_all(players)
        self.open_voting(players)

        civilian = next(player for player in players if player["player_id"] not in room.varalica_ids)
        invalid = self.vote(civilian, [room.varalica_ids[0]])
        self.assertEqual(invalid.status_code, 400)
        self.assertNotIn(civilian["player_id"], room.final_votes)

        impostor_set = set(room.varalica_ids)
        civilian_ids = [player["player_id"] for player in players if player["player_id"] not in impostor_set]
        for player in players:
            if player["player_id"] in impostor_set:
                other = next(item for item in room.varalica_ids if item != player["player_id"])
                targets = [other, civilian_ids[0]]
            else:
                targets = list(room.varalica_ids)
            response = self.vote(player, targets)
            self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(room.state, "voting_complete")
        self.assertTrue(main.players_caught_all_varalice(room))

        reveal = self.client.post(
            f"/api/rooms/{room.code}/reveal",
            json={"player_id": players[0]["player_id"]},
            headers=self.auth(players[0]),
        )
        self.assertEqual(reveal.status_code, 200, reveal.text)
        results = main.results_state(room, players[0]["player_id"])
        self.assertEqual(results["varalica_count"], 2)
        self.assertTrue(results["was_varalica_caught"])
        for player_id in civilian_ids:
            self.assertEqual(room.scoreboard[player_id]["discoveries"], 1)
        for player_id in room.varalica_ids:
            self.assertEqual(room.scoreboard[player_id]["survivals"], 0)

    def test_every_supported_room_size_and_mid_round_spectator(self):
        for count in range(main.MIN_PLAYERS, main.MAX_PLAYERS + 1):
            with self.subTest(player_count=count):
                players = self.create_group(count)
                room = self.start_round(players, varalica_count=2)
                self.assertEqual(len(room.round_player_ids), count)
                self.assertEqual(len(room.varalica_ids), 2 if count >= 7 else 1)
                main.rooms.pop(room.code)

        players = self.create_group(4)
        room = self.start_round(players)
        spectator_response = self.client.post(
            f"/api/rooms/{room.code}/join",
            json={"name": "Spectator", "play_mode": "live", "ui_language": "de"},
        )
        self.assertEqual(spectator_response.status_code, 200, spectator_response.text)
        spectator = spectator_response.json()
        self.assertTrue(spectator["spectator"])
        self.assertNotIn(spectator["player_id"], room.round_player_ids)
        self.assertTrue(main.public_state(room, spectator["player_id"])["viewer_is_spectator"])

        room.state = "results"
        next_round = self.client.post(
            f"/api/rooms/{room.code}/new-round",
            json={"player_id": players[0]["player_id"]},
            headers=self.auth(players[0]),
        )
        self.assertEqual(next_round.status_code, 200, next_round.text)
        self.assertIn(spectator["player_id"], room.round_player_ids)
        self.assertFalse(main.public_state(room, spectator["player_id"])["viewer_is_spectator"])

    def test_tie_runs_two_overtimes_then_allows_reveal(self):
        players = self.create_group(4)
        room = self.start_round(players)
        self.confirm_all(players)
        self.open_voting(players)
        ids = [player["player_id"] for player in players]
        cycle = {ids[0]: ids[1], ids[1]: ids[0], ids[2]: ids[3], ids[3]: ids[2]}

        for expected_overtime in (1, 2):
            for player in players:
                response = self.vote(player, [cycle[player["player_id"]]])
                self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(room.state, "overtime")
            self.assertEqual(room.overtime_count, expected_overtime)
            main.stop_timer(room)
            opened = self.client.post(
                f"/api/rooms/{room.code}/open-final-voting",
                json={"player_id": players[0]["player_id"]},
                headers=self.auth(players[0]),
            )
            self.assertEqual(opened.status_code, 200, opened.text)
            self.assertEqual(room.state, "overtime_voting")

        for player in players:
            response = self.vote(player, [cycle[player["player_id"]]])
            self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(room.state, "voting_complete")
        self.assertEqual(room.overtime_count, main.MAX_OVERTIME_ROUNDS)
        self.assertTrue(main.is_vote_tied(room))
        self.assertTrue(main.voting_complete_state(room)["can_reveal"])

        reveal = self.client.post(
            f"/api/rooms/{room.code}/reveal",
            json={"player_id": players[0]["player_id"]},
            headers=self.auth(players[0]),
        )
        self.assertEqual(reveal.status_code, 200, reveal.text)
        self.assertEqual(room.state, "results")
        self.assertFalse(main.results_state(room, players[0]["player_id"])["was_varalica_caught"])
        self.assertEqual(room.scoreboard[room.varalica_id]["survivals"], 1)

    def test_websocket_sync_reconnect_and_host_departure(self):
        players = self.create_group(4)
        room = main.rooms[players[0]["room_code"]]
        first_url = f"/ws/{room.code}/{players[0]['player_id']}"
        second_url = f"/ws/{room.code}/{players[1]['player_id']}"
        with self.client.websocket_connect(first_url) as first:
            first.send_json({"type": "auth", "credential": players[0]["credential"], "language": "hr"})
            first.receive_json()
            with self.client.websocket_connect(second_url) as second:
                second.send_json({"type": "auth", "credential": players[1]["credential"], "language": "de"})
                second.receive_json()
                first.receive_json()
                transferred = self.client.post(
                    f"/api/rooms/{room.code}/transfer-host",
                    json={"player_id": players[0]["player_id"], "target_id": players[1]["player_id"]},
                    headers=self.auth(players[0]),
                )
                self.assertEqual(transferred.status_code, 200, transferred.text)
                first_state = first.receive_json()
                second_state = second.receive_json()
                self.assertEqual(first_state["host_id"], players[1]["player_id"])
                self.assertEqual(second_state["host_id"], players[1]["player_id"])
                self.assertEqual(first_state["players"], second_state["players"])

        before_count = len(room.players)
        reconnected = self.client.post(
            f"/api/rooms/{room.code}/join",
            json={
                "name": "Player 1 Back",
                "player_id": players[0]["player_id"],
                "play_mode": "live",
                "ui_language": "tr",
            },
            headers=self.auth(players[0]),
        )
        self.assertEqual(reconnected.status_code, 200, reconnected.text)
        self.assertEqual(reconnected.json()["player_id"], players[0]["player_id"])
        self.assertNotIn("credential", reconnected.json())
        self.assertEqual(len(room.players), before_count)
        self.assertEqual(room.players[players[0]["player_id"]].ui_language, "tr")

        leaving_host = self.client.post(
            f"/api/rooms/{room.code}/leave",
            json={"player_id": players[1]["player_id"]},
            headers=self.auth(players[1]),
        )
        self.assertEqual(leaving_host.status_code, 200, leaving_host.text)
        self.assertNotIn(players[1]["player_id"], room.players)
        self.assertIn(room.host_id, room.players)
        self.assertEqual(sum(player.is_host for player in room.players.values()), 1)

    def test_discussion_timer_is_identical_for_all_viewers(self):
        players = self.create_group(4, mode="chat")
        room = self.start_round(players)
        self.confirm_all(players)
        fixed_now = time.time()
        room.discussion_started_at = fixed_now - 42
        with patch("main.time.time", return_value=fixed_now):
            states = [main.public_state(room, player["player_id"]) for player in players]
        discussions = [state["discussion"] for state in states]
        self.assertTrue(all(discussion == discussions[0] for discussion in discussions))
        self.assertEqual(discussions[0]["remaining_seconds"], 78)
        self.assertEqual(discussions[0]["current_player_id"], main.current_player_id(room))
        self.assertTrue(all(state["play_mode"] == "chat" for state in states))

    def test_kick_invalidates_the_removed_seat_and_credential(self):
        players = self.create_group(4)
        room = main.rooms[players[0]["room_code"]]
        target = players[1]
        kicked = self.client.post(
            f"/api/rooms/{room.code}/kick",
            json={"player_id": players[0]["player_id"], "target_id": target["player_id"]},
            headers=self.auth(players[0]),
        )
        self.assertEqual(kicked.status_code, 200, kicked.text)
        self.assertNotIn(target["player_id"], room.players)
        self.assertIn(target["player_id"], room.kicked_player_ids)

        rejected = self.client.post(
            f"/api/rooms/{room.code}/join",
            json={
                "name": "Kicked Back",
                "player_id": target["player_id"],
                "play_mode": "live",
                "ui_language": "hr",
            },
            headers=self.auth(target),
        )
        self.assertEqual(rejected.status_code, 401, rejected.text)
        self.assertNotIn(target["player_id"], room.players)

    def test_vote_rejects_duplicate_self_and_second_submission(self):
        players = self.create_group(7)
        room = self.start_round(players, varalica_count=2)
        self.confirm_all(players)
        self.open_voting(players)
        voter = players[0]
        other_ids = [player["player_id"] for player in players[1:]]

        duplicate = self.vote(voter, [other_ids[0], other_ids[0]])
        self.assertEqual(duplicate.status_code, 400, duplicate.text)
        self.assertNotIn(voter["player_id"], room.final_votes)

        self_vote = self.vote(voter, [voter["player_id"], other_ids[0]])
        self.assertEqual(self_vote.status_code, 400, self_vote.text)
        self.assertNotIn(voter["player_id"], room.final_votes)

        accepted = self.vote(voter, other_ids[:2])
        self.assertEqual(accepted.status_code, 200, accepted.text)
        second_vote = self.vote(voter, other_ids[2:4])
        self.assertEqual(second_vote.status_code, 400, second_vote.text)
        self.assertEqual(room.final_votes[voter["player_id"]], other_ids[:2])

    def test_change_word_is_allowed_in_reveal_and_only_before_discussion_deadline(self):
        reveal_players = self.create_group(4)
        reveal_room = self.start_round(reveal_players)
        reveal_word_id = reveal_room.current_word_id
        reveal_change = self.client.post(
            f"/api/rooms/{reveal_room.code}/change-word",
            json={"player_id": reveal_players[0]["player_id"]},
            headers=self.auth(reveal_players[0]),
        )
        self.assertEqual(reveal_change.status_code, 200, reveal_change.text)
        self.assertEqual(reveal_room.state, "reveal")
        self.assertNotEqual(reveal_room.current_word_id, reveal_word_id)

        for elapsed, expected_status in ((9.999, 200), (10.0, 400), (10.001, 400)):
            with self.subTest(elapsed=elapsed):
                players = self.create_group(4)
                room = self.start_round(players)
                self.confirm_all(players)
                room.discussion_started_at = 1_000.0
                with patch("main.time.time", return_value=1_000.0 + elapsed):
                    response = self.client.post(
                        f"/api/rooms/{room.code}/change-word",
                        json={"player_id": players[0]["player_id"]},
                        headers=self.auth(players[0]),
                    )
                self.assertEqual(response.status_code, expected_status, response.text)
                self.assertEqual(room.state, "reveal" if expected_status == 200 else "discussion")

    def test_expired_tab_close_removes_player_without_corrupting_round(self):
        players = self.create_group(4)
        room = self.start_round(players)
        self.confirm_all(players)
        removed_id = players[1]["player_id"]
        fixed_now = time.time()
        room.players[removed_id].likely_tab_closed_at = fixed_now - main.TAB_CLOSE_REMOVE_SECONDS
        room.players[removed_id].last_seen_at = fixed_now - main.TAB_CLOSE_REMOVE_SECONDS
        with patch("main.time.time", return_value=fixed_now):
            expired_ids = main.cleanup_expired_disconnected_players(room)

        self.assertEqual(expired_ids, [removed_id])
        self.assertNotIn(removed_id, room.players)
        self.assertNotIn(removed_id, room.round_player_ids)
        self.assertNotEqual(room.host_id, removed_id)
        self.assertIn(main.current_player_id(room), room.round_player_ids)

    def test_empty_room_cleanup_deletes_only_its_snapshot_and_history(self):
        players = self.create_group(1)
        room = main.rooms[players[0]["room_code"]]
        storage.save_used_word_index(room.code, 17)
        main.remove_player_from_room(room, players[0]["player_id"])
        room.empty_since = time.time()
        with patch("main.asyncio.sleep", new=AsyncMock()):
            asyncio.run(main.empty_room_cleanup_loop(room.code))
        self.assertNotIn(room.code, main.rooms)
        self.assertEqual(storage.load_used_word_indexes(room.code), set())
        self.assertNotIn(room.code, storage.load_room_snapshots())


if __name__ == "__main__":
    unittest.main()
