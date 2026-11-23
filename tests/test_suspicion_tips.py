import json
import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

import main


class SuspicionTipTests(unittest.TestCase):
    def setUp(self):
        self.original_persist = main.persist_room
        self.persists = 0

        def persist(room):
            self.persists += 1

        main.persist_room = persist
        self.client = TestClient(main.app)
        self.client.__enter__()
        self.codes = []

    def tearDown(self):
        self.client.__exit__(None, None, None)
        for code in self.codes:
            main.rooms.pop(code, None)
        main.persist_room = self.original_persist

    def create_player(self, name, room_code=None, mode="live"):
        if room_code is None:
            response = self.client.post("/api/rooms", json={"name": name, "play_mode": mode})
        else:
            response = self.client.post(f"/api/rooms/{room_code}/join", json={"name": name, "play_mode": mode})
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        if data["room_code"] not in self.codes:
            self.codes.append(data["room_code"])
        return data

    def auth(self, credential):
        return {"Authorization": f"Bearer {credential}"}

    def players(self, count, mode="live"):
        names = ["Ana", "Marko", "Iva", "Luka", "Petra", "Nikola", "Teo", "Sara"]
        host = self.create_player(names[0], mode=mode)
        group = [host]
        for name in names[1:count]:
            group.append(self.create_player(name, host["room_code"], mode))
        return group

    def open_discussion(self, group, duration=120, impostors=1):
        room = main.rooms[group[0]["room_code"]]
        room.state = "discussion"
        room.discussion_duration_seconds = duration
        room.discussion_started_at = time.time()
        room.final_discussion_started_at = None
        room.round_player_ids = [player["player_id"] for player in group]
        room.play_mode = group[0].get("room_play_mode", room.play_mode)
        room.varalica_ids = room.round_player_ids[:impostors]
        room.varalica_id = room.varalica_ids[0]
        room.final_votes.clear()
        room.suspicion_tips.clear()
        return room

    def open_final_discussion(self, group, duration=120, seconds_into_final=1, impostors=1):
        room = self.open_discussion(group, duration, impostors)
        now = time.time()
        room.discussion_started_at = now - duration - seconds_into_final
        room.final_discussion_started_at = room.discussion_started_at + duration
        return room

    def tip(self, group_player, target_id, credential=None):
        return self.client.post(
            f"/api/rooms/{group_player['room_code']}/suspicion",
            json={"player_id": group_player["player_id"], "target_id": target_id},
            headers=self.auth(credential or group_player["credential"]),
        )

    def test_rounding_is_deterministic(self):
        self.assertEqual(main.suspicion_percent(0, 0), 0)
        self.assertEqual(main.suspicion_percent(0, 4), 0)
        self.assertEqual(main.suspicion_percent(1, 1), 100)
        self.assertEqual(main.suspicion_percent(1, 2), 50)
        self.assertEqual(main.suspicion_percent(1, 3), 33)
        self.assertEqual(main.suspicion_percent(2, 3), 67)
        self.assertEqual(main.suspicion_percent(1, 6), 17)

    def test_assign_transfer_and_same_target_noop(self):
        group = self.players(4)
        room = self.open_final_discussion(group)
        first = self.tip(group[0], group[1]["player_id"])
        self.assertEqual(first.status_code, 200)
        self.assertEqual(room.suspicion_tips[group[0]["player_id"]], group[1]["player_id"])
        persisted = self.persists
        same = self.tip(group[0], group[1]["player_id"])
        self.assertEqual(same.status_code, 200)
        self.assertTrue(same.json()["unchanged"])
        self.assertEqual(self.persists, persisted)
        moved = self.tip(group[0], group[2]["player_id"])
        self.assertEqual(moved.status_code, 200)
        self.assertEqual(room.suspicion_tips, {group[0]["player_id"]: group[2]["player_id"]})
        state = main.public_state(room, group[0]["player_id"])
        self.assertEqual(state["players"][0]["suspicion_percent"] if False else state["viewer_suspicion_target_id"], group[2]["player_id"])
        percents = {player["id"]: player["suspicion_percent"] for player in state["players"]}
        self.assertEqual(percents[group[2]["player_id"]], 100)
        self.assertEqual(percents[group[1]["player_id"]], 0)

    def test_rejections(self):
        group = self.players(4)
        room = self.open_final_discussion(group)
        outsider = self.players(1)
        url_player = group[0]
        self.assertEqual(self.client.post(
            f"/api/rooms/{url_player['room_code']}/suspicion",
            json={"player_id": url_player["player_id"], "target_id": group[1]["player_id"]},
        ).status_code, 401)
        self.assertEqual(self.tip(url_player, group[1]["player_id"], "wrong-token").status_code, 401)
        self.assertEqual(self.tip(url_player, group[1]["player_id"], outsider[0]["credential"]).status_code, 401)
        self.assertEqual(self.tip(url_player, url_player["player_id"]).status_code, 400)
        self.assertEqual(self.tip(url_player, "missing-player").status_code, 400)
        room.round_player_ids = [player["player_id"] for player in group[1:]]
        self.assertEqual(self.tip(url_player, group[1]["player_id"]).status_code, 400)
        self.assertEqual(room.suspicion_tips, {})

    def test_percentages_transfer_and_privacy(self):
        group = self.players(4, "chat")
        room = self.open_final_discussion(group)
        self.assertEqual(self.tip(group[0], group[2]["player_id"]).status_code, 200)
        self.assertEqual(self.tip(group[1], group[2]["player_id"]).status_code, 200)
        self.assertEqual(self.tip(group[0], group[3]["player_id"]).status_code, 200)
        viewer = main.public_state(room, group[0]["player_id"])
        other = main.public_state(room, group[1]["player_id"])
        self.assertEqual(viewer["viewer_suspicion_target_id"], group[3]["player_id"])
        self.assertEqual(other["viewer_suspicion_target_id"], group[2]["player_id"])
        self.assertEqual(viewer["suspicion_total"], 2)
        percents = {player["id"]: player["suspicion_percent"] for player in viewer["players"]}
        self.assertEqual(percents[group[3]["player_id"]], 50)
        self.assertEqual(percents[group[2]["player_id"]], 50)
        encoded = json.dumps(viewer)
        self.assertNotIn("suspicion_tips", encoded)
        self.assertNotIn(group[0]["credential"], encoded)
        self.assertNotIn(room.players[group[0]["player_id"]].credential_verifier, encoded)

    def test_parallel_tips_keep_one_entry_per_player(self):
        group = self.players(4)
        self.open_final_discussion(group)

        def send(player, target):
            return self.tip(player, target).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(send, (group[0], group[1]), (group[2]["player_id"], group[3]["player_id"])))
        self.assertEqual(statuses, [200, 200])
        room = main.rooms[group[0]["room_code"]]
        self.assertEqual(len(room.suspicion_tips), 2)
        self.assertEqual(room.final_votes, {})

    def test_snapshot_removal_host_transfer_and_reset(self):
        group = self.players(4)
        room = self.open_final_discussion(group)
        self.assertEqual(self.tip(group[0], group[1]["player_id"]).status_code, 200)
        self.assertEqual(self.tip(group[1], group[0]["player_id"]).status_code, 200)
        snapshot = main.room_to_snapshot(room)
        self.assertEqual(snapshot["suspicion_tips"][group[0]["player_id"]], group[1]["player_id"])
        main.rooms.pop(room.code)
        restored = main.room_from_snapshot(snapshot)
        main.rooms[restored.code] = restored
        self.assertEqual(main.public_state(restored, group[0]["player_id"])["viewer_suspicion_target_id"], group[1]["player_id"])
        main.set_host(restored, group[2]["player_id"])
        self.assertEqual(restored.suspicion_tips[group[0]["player_id"]], group[1]["player_id"])
        left = self.client.post(
            f"/api/rooms/{restored.code}/leave",
            json={"player_id": group[1]["player_id"]},
            headers=self.auth(group[1]["credential"]),
        )
        self.assertEqual(left.status_code, 200)
        self.assertNotIn(group[1]["player_id"], restored.suspicion_tips)
        self.assertNotIn(group[1]["player_id"], restored.suspicion_tips.values())
        main.reset_room_to_lobby(restored)
        self.assertEqual(restored.suspicion_tips, {})

    def test_blocked_phases_and_unchanged_timers(self):
        self.assertEqual(main.FINAL_DISCUSSION_SECONDS, 30)
        self.assertEqual(main.OVERTIME_SECONDS, 30)
        group = self.players(4)
        room = self.open_discussion(group, 120)
        room.discussion_started_at = time.time() - 130
        room.final_discussion_started_at = time.time() - 10
        self.assertTrue(main.suspicion_submissions_open(room))
        self.assertEqual(self.tip(group[0], group[1]["player_id"]).status_code, 200)
        room.final_discussion_started_at = time.time() - 30.2
        self.assertFalse(main.suspicion_submissions_open(room))
        self.assertEqual(self.tip(group[0], group[2]["player_id"]).status_code, 400)
        for state in ("final_voting", "overtime", "overtime_voting", "reveal", "results"):
            room.state = state
            self.assertEqual(self.tip(group[0], group[2]["player_id"]).status_code, 400, state)
        room.state = "overtime"
        room.overtime_started_at = time.time()
        self.assertTrue(main.overtime_voting_unlocked(room))
        self.assertEqual(room.final_votes, {})

    def test_tips_do_not_change_one_or_two_impostor_results(self):
        for impostors, count in ((1, 4), (2, 7)):
            group = self.players(count)
            room = self.open_final_discussion(group, impostors=impostors)
            self.assertEqual(len(room.varalica_ids), impostors)
            for player in group:
                target = next(item["player_id"] for item in group if item["player_id"] != player["player_id"])
                self.assertEqual(self.tip(player, target).status_code, 200)
            self.assertEqual(len(room.suspicion_tips), count)
            room.state = "results"
            room.final_votes = {group[0]["player_id"]: list(room.varalica_ids)}
            caught_before = main.players_caught_all_varalice(room)
            room.suspicion_tips[group[0]["player_id"]] = group[1]["player_id"]
            self.assertEqual(main.players_caught_all_varalice(room), caught_before)
            self.assertEqual(room.final_votes[group[0]["player_id"]], list(room.varalica_ids))

    def test_only_the_final_discussion_accepts_tips(self):
        for mode in ("live", "chat"):
            for duration in (120, 180, 300):
                group = self.players(4, mode)
                room = self.open_discussion(group, duration)
                room.discussion_started_at = time.time() - (duration - 5)
                early = self.tip(group[0], group[1]["player_id"])
                self.assertEqual(early.status_code, 400, (mode, duration))
                self.assertFalse(main.public_state(room, group[0]["player_id"])["suspicion_open"])
                self.assertEqual(room.final_votes, {})
                self.assertEqual(main.FINAL_DISCUSSION_SECONDS, 30)
                room.discussion_started_at = time.time() - duration - 0.2
                room.final_discussion_started_at = None
                self.assertEqual(self.tip(group[0], group[1]["player_id"]).status_code, 200)
                self.assertTrue(main.suspicion_submissions_open(room))
                room.final_discussion_started_at = time.time() - 10
                self.assertEqual(self.tip(group[0], group[2]["player_id"]).status_code, 200)
                room.final_discussion_started_at = time.time() - 30.2
                self.assertEqual(self.tip(group[0], group[3]["player_id"]).status_code, 400)
                self.assertNotIn(group[3]["player_id"], room.suspicion_tips.values())
                vote = self.client.post(
                    f"/api/rooms/{room.code}/vote",
                    json={"player_id": group[0]["player_id"], "target_id": group[1]["player_id"], "target_ids": [group[1]["player_id"]]},
                    headers=self.auth(group[0]["credential"]),
                )
                self.assertEqual(vote.status_code, 400)
                self.assertEqual(room.final_votes, {})
        self.assertEqual(main.OVERTIME_SECONDS, 30)

    def test_next_player_locks_when_regular_discussion_expires(self):
        group = self.players(4)
        room = self.open_discussion(group, 120)
        room.host_id = group[0]["player_id"]
        room.current_player_index = 0
        self.assertTrue(main.next_player_allowed(room))
        response = self.client.post(
            f"/api/rooms/{room.code}/next-player",
            json={"player_id": group[0]["player_id"]},
            headers=self.auth(group[0]["credential"]),
        )
        self.assertEqual(response.status_code, 200, response.text)
        room.discussion_started_at = time.time() - 120
        self.assertFalse(main.next_player_allowed(room))
        self.assertFalse(main.suspicion_submissions_open(room) and main.final_discussion_seconds_left(room) == 0)
        late = self.client.post(
            f"/api/rooms/{room.code}/next-player",
            json={"player_id": group[0]["player_id"]},
            headers=self.auth(group[0]["credential"]),
        )
        self.assertEqual(late.status_code, 400, late.text)
        self.assertTrue(main.suspicion_submissions_open(room))
        self.assertEqual(main.final_discussion_seconds_left(room), 30)

    def test_percentages_stay_until_results_and_reset_next_round(self):
        group = self.players(4)
        room = self.open_final_discussion(group)
        self.assertEqual(self.tip(group[0], group[1]["player_id"]).status_code, 200)
        frozen = {player["id"]: player["suspicion_percent"] for player in main.public_state(room, group[0]["player_id"])["players"]}
        room.final_discussion_started_at = time.time() - 30.2
        locked = main.public_state(room, group[0]["player_id"])
        self.assertFalse(locked["suspicion_open"])
        self.assertTrue(locked["suspicion_visible"])
        self.assertEqual({player["id"]: player["suspicion_percent"] for player in locked["players"]}, frozen)
        self.assertEqual(self.tip(group[0], group[2]["player_id"]).status_code, 400)
        for state in ("final_voting", "voting_complete", "overtime", "overtime_voting"):
            room.state = state
            visible = main.public_state(room, group[0]["player_id"])
            self.assertTrue(visible["suspicion_visible"], state)
            self.assertFalse(visible["suspicion_open"], state)
            self.assertEqual(self.tip(group[0], group[2]["player_id"]).status_code, 400, state)
            self.assertEqual({player["id"]: player["suspicion_percent"] for player in visible["players"]}, frozen)
        room.state = "results"
        hidden = main.public_state(room, group[0]["player_id"])
        self.assertFalse(hidden["suspicion_visible"])
        self.assertEqual(hidden["viewer_suspicion_target_id"], None)
        self.assertTrue(all(player["suspicion_percent"] == 0 for player in hidden["players"]))
        main.prepare_reveal_round(room, list(room.players.values())[:4])
        self.assertEqual(room.suspicion_tips, {})
        self.assertFalse(main.public_state(room, group[0]["player_id"])["suspicion_visible"])


if __name__ == "__main__":
    unittest.main()
