# Varalica

Mobile-first multiplayer web app for the Balkan party game "Varalica".

## Implemented scope

Implemented:

- FastAPI backend
- WebSocket room sync
- Mobile-first dark frontend
- Create room
- Join room by code or `/room/{code}` link
- Player name input
- Optional emoji avatar selection with 30 predefined avatars
- Player list
- Host role
- Minimum 4 and maximum 10 player validation
- Host-only start round
- Random Varalica selection
- Random starter word selection
- Private Varalica hint for every word
- Private role/word screen
- "Prikazi moju rijec"
- "OK, vidio sam"
- Per-player readiness badges
- Backend validation before confirming
- Exactly 1000 structured word entries
- Per-room used-word tracking with random non-repeating selection
- SQLite persistence for per-room used-word history
- Automatic discussion phase after all active players confirm
- Backend-authoritative 3-minute discussion timer
- Current active player tracking
- Host-only "Sljedeći igrač"
- Voting locked for the first 100 seconds
- Vote request tracking
- `ready_for_final_voting` state after all active players request voting
- Host opens final voting
- One final vote per active player
- Voting status without revealing individual votes
- Voting-complete screen after all active players vote
- Result summary with vote counts and winner message
- One 60-second overtime discussion after the first tied final vote
- Automatic second voting round after overtime
- Host-only manual reveal after voting is complete
- Public vote target display in the player list
- Persistent localStorage player session
- Persistent avatar after refresh, reconnect, and new round
- 10-minute reconnect grace period for mobile disconnects
- Explicit Leave room action
- Host-only new round from the same room
- SQLite persistence for active room snapshots
- Reconnect support after server restart for existing room/player tabs

Not implemented yet:

- Admin cleanup for old room snapshots

## Run locally

```powershell
cd D:\Projects\Varalica_webapp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open:

```text
http://localhost:8000
```

## Manual test with 4 browser tabs

1. Open `http://localhost:8000` in tab 1.
2. Enter a name and create a room.
3. Copy the room link or code.
4. Open the link in three more tabs.
5. Join with three different names.
6. Confirm the host cannot start below 4 players.
7. Start the round as host after 4 players are present.
8. In each tab, click "Prikazi moju rijec".
9. Confirm one player sees "Ti si Varalica".
10. Confirm other players see only the Croatian/Serbian word pair.
11. Click "OK, vidio sam" in some tabs and watch readiness badges update live.
12. Confirm discussion starts automatically after all active round players click "OK, vidio sam".
13. Confirm the 3-minute timer updates live in all tabs.
14. Confirm the active player is highlighted green.
15. In the host tab, click "Sljedeći igrač" and confirm the green highlight rotates.
16. Confirm "Glasanje dostupno nakon 100 sekundi" is disabled before 100 seconds.
17. After 100 seconds, confirm only the host can click "Otvori glasanje".
18. Vote once in every tab.
19. Confirm voting status badges update before results.
20. Confirm each voter shows "Glasao/la za: [player]" in the player list.
21. Confirm results do not appear automatically after every active player votes.
22. Confirm only host sees "Prikaži Varalicu".
23. Host clicks "Prikaži Varalicu".
24. Confirm all players see Varalica, word, vote totals, and who voted for whom.
25. Confirm the host can click "Nova runda" and return everyone to reveal phase.

## New round test

1. Finish a round until results.
2. Host clicks "Nova runda".
3. Confirm the same room code remains visible.
4. Confirm the same players remain in the right-side list.
5. Confirm no invite/lobby screen appears.
6. Confirm all players move directly to the new reveal phase.
7. Confirm old votes, vote targets, ready badges, and result details are cleared.
8. Confirm idle players still inside the 10-minute reconnect grace period remain in the room and are included in the new round.
9. Confirm every player's avatar stays the same.

## Avatar test

1. Open the app and select an emoji avatar before creating or joining a room.
2. Join another player without selecting an avatar.
3. Confirm the second player receives a random avatar.
4. Confirm avatars appear in the lobby, player list, voting options, results, and "Ko je za koga glasao" list.
5. Refresh a player tab and confirm the avatar stays the same after reconnect.
6. Start a new round and confirm avatars do not change.

## Overtime tie test

1. Reach final voting with 4 browser tabs.
2. Vote 2:2 so the result is tied.
3. Confirm the app shows "Glasanje je neriješeno." without revealing Varalica.
4. In the host tab, click "Produži igru 60 sekundi".
5. Confirm the overtime timer starts and syncs to all tabs.
6. After 60 seconds, confirm voting opens again.
7. Vote again in all tabs.
8. If the second vote is tied, confirm the app waits for host to click "Prikaži Varalicu".
9. Confirm the revealed result says Varalica survived after overtime.

## Mobile reconnect test

1. Join a room from a phone.
2. Refresh the page and confirm the same player returns without creating a duplicate.
3. Lock the phone for 2-5 minutes, unlock, and confirm the same player reconnects.
4. Disable Wi-Fi briefly, re-enable it, and confirm the same player reconnects.
5. While disconnected, confirm the player appears with an Idle badge.
6. Leave a player disconnected for more than 10 minutes and confirm they are removed when the room updates.
7. Click "Leave room" and confirm the player leaves immediately and the local session is cleared.

## Privacy notes

The public room state does not include the secret word, the Varalica id, or other players' private roles. Each WebSocket receives a `private` field generated only for that connected player.

## Word history storage

Used words are stored per room in `varalica.sqlite3`. A room will not repeat a word until all 1000 words have been used. After the full pool is exhausted for that room, its used-word list is reset and a fresh random cycle starts.

## Room snapshot storage

Active room state is also stored in `varalica.sqlite3`. If the server restarts, existing tabs with the same room/player session can reconnect to the saved room. Players are restored as offline until their tab reconnects.

## Current limitations

- WebSocket connections and timer tasks are runtime-only and are recreated when the server starts or players reconnect.
- Old room snapshots are not automatically cleaned up yet.
