from __future__ import annotations

import asyncio
import random
import secrets
import string
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from storage import (
    delete_room_data,
    init_storage,
    load_room_snapshots,
    load_used_word_indexes,
    reset_selected_used_word_indexes,
    reset_used_word_indexes,
    save_room_snapshot,
    save_used_word_index,
)
from words import ALLOWED_CATEGORIES, DEFAULT_CATEGORY, STARTER_WORDS, normalize_category, words_for_category


MIN_PLAYERS = 4
MAX_PLAYERS = 10
DISCUSSION_SECONDS = 180
ALLOWED_DISCUSSION_SECONDS = {120, 180, 300}
VOTING_LOCK_SECONDS = 100
OVERTIME_SECONDS = 60
ACTIVE_GRACE_SECONDS = 30
AWAY_AFTER_SECONDS = 30
IDLE_AFTER_SECONDS = 180
REMOVE_AFTER_SECONDS = 300
RECONNECT_GRACE_SECONDS = REMOVE_AFTER_SECONDS
EMPTY_ROOM_CLEANUP_SECONDS = 300
ALLOWED_AVATARS = [
    "😀", "😎", "🤓", "🥳", "😇", "🤠", "🐵", "🦊", "🐼", "🐸",
    "🐱", "🐶", "🦁", "🐯", "🦄", "🐧", "🐙", "🦖", "👽", "🤖",
    "🧙‍♂️", "🧙‍♀️", "🦸‍♂️", "🦸‍♀️", "🕵️‍♂️", "🕵️‍♀️", "👑", "🎭", "🎲", "🔥",
]

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Varalica")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
async def startup() -> None:
    init_storage()
    load_persisted_rooms()
    for room in rooms.values():
        if room.state == "discussion" or (room.state == "overtime" and room.overtime_started_at is not None):
            room.timer_task = asyncio.create_task(timer_loop(room.code))
        if not room.players and room.empty_since is not None:
            room.empty_cleanup_task = asyncio.create_task(empty_room_cleanup_loop(room.code))
    asyncio.create_task(presence_monitor_loop())


class NameRequest(BaseModel):
    name: str
    avatar: str | None = None


class PlayerAction(BaseModel):
    player_id: str


class StartRoundAction(PlayerAction):
    category: str | None = None
    discussion_seconds: int | None = None


class VoteAction(BaseModel):
    player_id: str
    target_id: str


class TargetPlayerAction(PlayerAction):
    target_id: str


@dataclass
class Player:
    id: str
    name: str
    avatar: str = ""
    is_host: bool = False
    connected: bool = True
    viewed_secret: bool = False
    confirmed: bool = False
    requested_vote: bool = False
    has_voted: bool = False
    last_seen_at: float = field(default_factory=time.time)
    connection_state: str = "active"
    disconnect_started_at: float | None = None
    disconnected_at: float | None = None
    joined_at: float = field(default_factory=time.time)


@dataclass
class Room:
    code: str
    state: str = "lobby"
    players: dict[str, Player] = field(default_factory=dict)
    host_id: str | None = None
    varalica_id: str | None = None
    word: dict | None = None
    current_word_id: str | None = None
    selected_hint: str | None = None
    used_word_indexes: set[int] = field(default_factory=set)
    round_player_ids: list[str] = field(default_factory=list)
    discussion_started_at: float | None = None
    current_player_index: int = 0
    vote_request_player_ids: set[str] = field(default_factory=set)
    final_votes: dict[str, str] = field(default_factory=dict)
    overtime_started_at: float | None = None
    overtime_used: bool = False
    selected_category: str = DEFAULT_CATEGORY
    discussion_duration_seconds: int = DISCUSSION_SECONDS
    recent_varalica_ids: list[str] = field(default_factory=list)
    round_number: int = 1
    scoreboard: dict[str, dict[str, int]] = field(default_factory=dict)
    kicked_player_ids: set[str] = field(default_factory=set)
    last_event: dict | None = None
    empty_since: float | None = None
    empty_cleanup_task: asyncio.Task | None = None
    timer_task: asyncio.Task | None = None
    sockets: dict[str, WebSocket] = field(default_factory=dict)


rooms: dict[str, Room] = {}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/room/{room_code}")
async def room_page(room_code: str) -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/rooms/{room_code}/status")
async def room_status(room_code: str) -> dict:
    room = rooms.get(room_code.upper())
    if room is None or room.empty_since is not None and not room.players:
        raise HTTPException(status_code=404, detail="Soba je istekla.")
    cleanup_expired_disconnected_players(room)
    lifecycle = room_lifecycle(room)
    if lifecycle != "active":
        raise HTTPException(status_code=404, detail="Soba je istekla.")
    return {"ok": True, "room_code": room.code, "lifecycle": lifecycle}


@app.post("/api/rooms")
async def create_room(request: NameRequest) -> dict:
    name = clean_name(request.name)
    room_code = make_room_code()
    room = Room(
        code=room_code,
        used_word_indexes=load_used_word_indexes(room_code),
    )
    player = Player(
        id=str(uuid.uuid4()),
        name=name,
        avatar=choose_avatar(room, request.avatar),
        is_host=True,
    )
    room.host_id = player.id
    room.players[player.id] = player
    ensure_scoreboard_player(room, player.id)
    rooms[room_code] = room
    persist_room(room)
    return {"room_code": room_code, "player_id": player.id, "avatar": player.avatar}


@app.post("/api/rooms/{room_code}/join")
async def join_room(room_code: str, request: NameRequest) -> dict:
    room = get_room(room_code)
    if not room.players and room.empty_since is not None:
        raise HTTPException(status_code=404, detail="Soba je istekla.")
    if len(room.players) >= MAX_PLAYERS:
        raise HTTPException(status_code=400, detail="Soba je puna. Maksimalno 10 igraca.")
    if room.state != "lobby":
        raise HTTPException(status_code=400, detail="Runda je vec pocela.")

    player = Player(
        id=str(uuid.uuid4()),
        name=clean_name(request.name),
        avatar=choose_avatar(room, request.avatar),
        is_host=not bool(room.players),
    )
    if player.is_host:
        room.host_id = player.id
    room.players[player.id] = player
    ensure_scoreboard_player(room, player.id)
    set_room_event(room, "join", player)
    persist_room(room)
    await broadcast_room(room)
    return {"room_code": room.code, "player_id": player.id, "avatar": player.avatar}


@app.post("/api/rooms/{room_code}/start")
async def start_round(room_code: str, action: StartRoundAction) -> dict:
    room = get_room(room_code)
    ensure_host(room, action.player_id)
    if room.state != "lobby":
        raise HTTPException(status_code=400, detail="Runda je vec pokrenuta.")

    cleanup_expired_disconnected_players(room)
    active_players = [player for player in room.players.values() if is_player_active_for_round(player)]
    if len(active_players) < MIN_PLAYERS:
        raise HTTPException(status_code=400, detail="Potrebna su najmanje 4 igraca.")
    if len(active_players) > MAX_PLAYERS:
        raise HTTPException(status_code=400, detail="Maksimalno je 10 igraca.")

    for player in room.players.values():
        player.viewed_secret = False
        player.confirmed = False
        player.requested_vote = False
        player.has_voted = False

    room.selected_category = normalize_category(action.category)
    room.discussion_duration_seconds = normalize_discussion_seconds(action.discussion_seconds)
    prepare_reveal_round(room, active_players)
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/view-secret")
async def view_secret(room_code: str, action: PlayerAction) -> dict:
    room = get_room(room_code)
    if room.state != "reveal":
        raise HTTPException(status_code=400, detail="Trenutno nije faza otkrivanja.")
    if action.player_id not in room.round_player_ids:
        raise HTTPException(status_code=400, detail="Igrac nije dio ove runde.")

    room.players[action.player_id].viewed_secret = True
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/change-word")
async def change_word(room_code: str, action: PlayerAction) -> dict:
    room = get_room(room_code)
    ensure_host(room, action.player_id)
    if room.state != "reveal":
        raise HTTPException(status_code=400, detail="Riječ se može promijeniti samo prije početka diskusije.")
    if room.varalica_id is None:
        raise HTTPException(status_code=400, detail="Runda nije spremna.")

    room.current_word_id = None
    room.selected_hint = None
    room.word = choose_word(room)
    for player_id in active_round_player_ids(room):
        player = room.players.get(player_id)
        if player is not None:
            player.viewed_secret = False
            player.confirmed = False
    if not selected_word_matches_room(room):
        raise HTTPException(status_code=500, detail="Nova riječ i hint nisu usklađeni.")
    set_room_event(room, "change_word", room.players[action.player_id])
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/confirm")
async def confirm_seen(room_code: str, action: PlayerAction) -> dict:
    room = get_room(room_code)
    if room.state != "reveal":
        raise HTTPException(status_code=400, detail="Trenutno nije faza otkrivanja.")
    if action.player_id not in room.round_player_ids:
        raise HTTPException(status_code=400, detail="Igrac nije dio ove runde.")

    room.players[action.player_id].confirmed = True
    if all_active_players_confirmed(room):
        await enter_discussion(room)
    else:
        persist_room(room)
        await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/next-player")
async def next_player(room_code: str, action: PlayerAction) -> dict:
    room = get_room(room_code)
    if room.state == "overtime" and room.overtime_started_at is None:
        raise HTTPException(status_code=400, detail="Produzetak jos nije pokrenut.")
    if room.state not in {"discussion", "overtime"}:
        raise HTTPException(status_code=400, detail="Trenutno nije faza diskusije.")

    active_ids = active_round_player_ids(room)
    if not active_ids:
        raise HTTPException(status_code=400, detail="Nema aktivnih igraca.")

    current_id = current_player_id(room)
    if action.player_id != room.host_id and action.player_id != current_id:
        raise HTTPException(status_code=403, detail="Samo host ili trenutni igrac mogu prebaciti red.")

    if current_id in active_ids:
        current_position = active_ids.index(current_id)
        next_id = active_ids[(current_position + 1) % len(active_ids)]
    else:
        next_id = active_ids[0]

    room.current_player_index = room.round_player_ids.index(next_id)
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/reset")
async def reset_room(room_code: str, action: PlayerAction) -> dict:
    room = get_room(room_code)
    ensure_host(room, action.player_id)
    reset_room_to_lobby(room)
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/kick")
async def kick_player(room_code: str, action: TargetPlayerAction) -> dict:
    room = get_room(room_code)
    ensure_host(room, action.player_id)
    if action.player_id == action.target_id:
        raise HTTPException(status_code=400, detail="Host ne moze izbaciti samog sebe.")
    target = room.players.get(action.target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Igrac nije u sobi.")

    socket = room.sockets.get(action.target_id)
    if socket is not None:
        try:
            await socket.send_json({"type": "kicked", "message": "Izbaceni ste iz sobe."})
            await socket.close(code=1008)
        except RuntimeError:
            pass

    room.kicked_player_ids.add(action.target_id)
    remove_player_from_room(room, action.target_id)
    await reconcile_after_player_removed(room)
    if not room.players:
        schedule_empty_room_cleanup(room)
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/transfer-host")
async def transfer_host(room_code: str, action: TargetPlayerAction) -> dict:
    room = get_room(room_code)
    ensure_host(room, action.player_id)
    if action.target_id not in room.players:
        raise HTTPException(status_code=404, detail="Igrac nije u sobi.")
    if action.target_id in room.kicked_player_ids:
        raise HTTPException(status_code=400, detail="Igrac vise nije u sobi.")
    set_host(room, action.target_id)
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/request-vote")
async def request_vote(room_code: str, action: PlayerAction) -> dict:
    get_room(room_code)
    raise HTTPException(status_code=400, detail="Glasanje otvara samo host nakon 100 sekundi.")


@app.post("/api/rooms/{room_code}/open-final-voting")
async def open_final_voting(room_code: str, action: PlayerAction) -> dict:
    room = get_room(room_code)
    ensure_host(room, action.player_id)
    if room.state == "discussion":
        if not voting_unlocked(room):
            raise HTTPException(status_code=400, detail="Glasanje dostupno nakon 100 sekundi.")
        stop_timer(room)
    elif room.state != "ready_for_final_voting":
        raise HTTPException(status_code=400, detail="Finalno glasanje jos nije spremno.")

    room.state = "final_voting"
    room.final_votes.clear()
    for player in room.players.values():
        player.has_voted = False
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/reveal")
async def reveal_results(room_code: str, action: PlayerAction) -> dict:
    room = get_room(room_code)
    ensure_host(room, action.player_id)
    if room.state != "voting_complete":
        raise HTTPException(status_code=400, detail="Varalica se moze prikazati tek nakon glasanja.")
    if not all_active_players_voted(room):
        raise HTTPException(status_code=400, detail="Svi aktivni igraci moraju glasati.")

    update_scoreboard(room)
    room.state = "results"
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/vote")
async def submit_vote(room_code: str, action: VoteAction) -> dict:
    room = get_room(room_code)
    if room.state not in {"final_voting", "overtime_voting"}:
        raise HTTPException(status_code=400, detail="Ne mozes glasati prije finalnog glasanja.")
    if action.player_id not in active_round_player_ids(room):
        raise HTTPException(status_code=400, detail="Igrac nije aktivan u ovoj rundi.")
    if action.target_id not in active_round_player_ids(room):
        raise HTTPException(status_code=400, detail="Ne mozes glasati za tog igraca.")
    if action.player_id == action.target_id:
        raise HTTPException(status_code=400, detail="Ne mozes glasati za sebe.")
    if action.player_id in room.final_votes:
        raise HTTPException(status_code=400, detail="Vec si glasao.")

    room.final_votes[action.player_id] = action.target_id
    room.players[action.player_id].has_voted = True

    if all_active_players_voted(room):
        finish_voting(room)

    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/start-overtime")
async def start_overtime(room_code: str, action: PlayerAction) -> dict:
    room = get_room(room_code)
    ensure_host(room, action.player_id)
    if room.state != "voting_complete":
        raise HTTPException(status_code=400, detail="Produzetak je dostupan samo nakon zavrsenog glasanja.")
    if room.overtime_used:
        raise HTTPException(status_code=400, detail="Produzetak je vec iskoristen.")
    if not is_vote_tied(room):
        raise HTTPException(status_code=400, detail="Glasanje nije nerijeseno.")

    room.state = "overtime"
    room.overtime_used = True
    room.overtime_started_at = time.time()
    room.final_votes.clear()
    for player in room.players.values():
        player.has_voted = False
    normalize_current_player(room)
    stop_timer(room)
    room.timer_task = asyncio.create_task(timer_loop(room.code))
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/new-round")
async def new_round(room_code: str, action: PlayerAction) -> dict:
    room = get_room(room_code)
    ensure_host(room, action.player_id)
    if room.state != "results":
        raise HTTPException(status_code=400, detail="Nova runda je dostupna tek nakon rezultata.")

    cleanup_expired_disconnected_players(room)
    active_players = [player for player in room.players.values() if is_player_active_for_round(player)]
    if len(active_players) < MIN_PLAYERS:
        raise HTTPException(status_code=400, detail="Potrebna su najmanje 4 aktivna igrača za novu rundu.")

    room.round_number += 1
    prepare_reveal_round(room, active_players)
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.post("/api/rooms/{room_code}/leave")
async def leave_room(room_code: str, action: PlayerAction) -> dict:
    room = get_room(room_code)
    if action.player_id not in room.players:
        raise HTTPException(status_code=404, detail="Igrac nije u sobi.")

    remove_player_from_room(room, action.player_id)
    await reconcile_after_player_removed(room)
    if not room.players:
        schedule_empty_room_cleanup(room)
    persist_room(room)
    await broadcast_room(room)
    return {"ok": True}


@app.websocket("/ws/{room_code}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, player_id: str) -> None:
    await websocket.accept()
    room = rooms.get(room_code.upper())
    if room is not None and player_id in room.kicked_player_ids:
        await websocket.send_json({"type": "kicked", "message": "Izbaceni ste iz sobe."})
        await websocket.close(code=1008)
        return
    if room is None or player_id not in room.players:
        await websocket.close(code=1008)
        return
    if time.time() - room.players[player_id].last_seen_at > RECONNECT_GRACE_SECONDS:
        remove_player_from_room(room, player_id)
        persist_room(room)
        await websocket.close(code=1008)
        return

    room.sockets[player_id] = websocket
    was_disconnected = not room.players[player_id].connected
    room.players[player_id].connected = True
    room.players[player_id].last_seen_at = time.time()
    room.players[player_id].connection_state = "active"
    room.players[player_id].disconnect_started_at = None
    room.players[player_id].disconnected_at = None
    cancel_empty_room_cleanup(room)
    if was_disconnected:
        set_room_event(room, "reconnect", room.players[player_id])
    persist_room(room)
    await broadcast_room(room)

    try:
        while True:
            await websocket.receive_text()
            if player_id in room.players:
                room.players[player_id].last_seen_at = time.time()
                room.players[player_id].connection_state = "active"
    except WebSocketDisconnect:
        if room.sockets.get(player_id) is websocket:
            del room.sockets[player_id]
        if player_id in room.players:
            room.players[player_id].connected = False
            now = time.time()
            room.players[player_id].disconnect_started_at = now
            room.players[player_id].disconnected_at = now
            room.players[player_id].connection_state = "away"
            asyncio.create_task(disconnected_player_status_loop(room.code, player_id))
        normalize_current_player(room)
        if room.state == "reveal" and all_active_players_confirmed(room):
            await enter_discussion(room)
        elif room.state == "discussion" and all_active_players_requested_vote(room):
            room.state = "ready_for_final_voting"
            stop_timer(room)
        elif room.state in {"final_voting", "overtime_voting"} and all_active_players_voted(room):
            finish_voting(room)
        elif room.state == "voting_complete" and not all_active_players_voted(room):
            room.state = "final_voting" if not room.overtime_used else "overtime_voting"
        persist_room(room)
        await broadcast_room(room)


def clean_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Unesi ime.")
    if len(cleaned) > 24:
        raise HTTPException(status_code=400, detail="Ime moze imati najvise 24 znaka.")
    return cleaned


def make_room_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choice(alphabet) for _ in range(5))
        if code not in rooms:
            return code


def get_room(room_code: str) -> Room:
    room = rooms.get(room_code.upper())
    if room is None:
        raise HTTPException(status_code=404, detail="Soba ne postoji.")
    return room


def ensure_host(room: Room, player_id: str) -> None:
    if room.host_id != player_id:
        raise HTTPException(status_code=403, detail="Samo host moze pokrenuti rundu.")


def choose_avatar(room: Room, requested_avatar: str | None) -> str:
    used_avatars = {player.avatar for player in room.players.values() if player.avatar}
    if requested_avatar in ALLOWED_AVATARS:
        if requested_avatar not in used_avatars or len(used_avatars) >= len(ALLOWED_AVATARS):
            return requested_avatar

    available_avatars = [avatar for avatar in ALLOWED_AVATARS if avatar not in used_avatars]
    return random.choice(available_avatars or ALLOWED_AVATARS)


def room_to_snapshot(room: Room) -> dict:
    return {
        "code": room.code,
        "state": room.state,
        "host_id": room.host_id,
        "varalica_id": room.varalica_id,
        "word": room.word,
        "current_word_id": room.current_word_id,
        "selected_hint": room.selected_hint,
        "round_player_ids": room.round_player_ids,
        "discussion_started_at": room.discussion_started_at,
        "current_player_index": room.current_player_index,
        "vote_request_player_ids": list(room.vote_request_player_ids),
        "final_votes": room.final_votes,
        "overtime_started_at": room.overtime_started_at,
        "overtime_used": room.overtime_used,
        "selected_category": room.selected_category,
        "discussion_duration_seconds": room.discussion_duration_seconds,
        "recent_varalica_ids": room.recent_varalica_ids,
        "round_number": room.round_number,
        "scoreboard": room.scoreboard,
        "kicked_player_ids": list(room.kicked_player_ids),
        "last_event": room.last_event,
        "empty_since": room.empty_since,
        "players": [
            {
                "id": player.id,
                "name": player.name,
                "avatar": player.avatar,
                "is_host": player.is_host,
                "connected": player.connected,
                "last_seen_at": player.last_seen_at,
                "connection_state": player.connection_state,
                "disconnect_started_at": player.disconnect_started_at,
                "viewed_secret": player.viewed_secret,
                "confirmed": player.confirmed,
                "requested_vote": player.requested_vote,
                "has_voted": player.has_voted,
                "disconnected_at": player.disconnected_at,
                "joined_at": player.joined_at,
            }
            for player in room.players.values()
        ],
    }


def room_from_snapshot(snapshot: dict) -> Room:
    room_code = str(snapshot["code"]).upper()
    room = Room(
        code=room_code,
        state=snapshot.get("state", "lobby"),
        host_id=snapshot.get("host_id"),
        varalica_id=snapshot.get("varalica_id"),
        word=snapshot.get("word"),
        current_word_id=snapshot.get("current_word_id") or (snapshot.get("word") or {}).get("id"),
        selected_hint=snapshot.get("selected_hint") or (snapshot.get("word") or {}).get("hint"),
        used_word_indexes=load_used_word_indexes(room_code),
        round_player_ids=list(snapshot.get("round_player_ids", [])),
        discussion_started_at=snapshot.get("discussion_started_at"),
        current_player_index=int(snapshot.get("current_player_index", 0)),
        vote_request_player_ids=set(snapshot.get("vote_request_player_ids", [])),
        final_votes=dict(snapshot.get("final_votes", {})),
        overtime_started_at=snapshot.get("overtime_started_at"),
        overtime_used=bool(snapshot.get("overtime_used", False)),
        selected_category=normalize_category(snapshot.get("selected_category")),
        discussion_duration_seconds=normalize_discussion_seconds(snapshot.get("discussion_duration_seconds")),
        recent_varalica_ids=list(snapshot.get("recent_varalica_ids", [])),
        round_number=int(snapshot.get("round_number", 1)),
        scoreboard=dict(snapshot.get("scoreboard", {})),
        kicked_player_ids=set(snapshot.get("kicked_player_ids", [])),
        last_event=snapshot.get("last_event"),
        empty_since=snapshot.get("empty_since"),
    )
    used_avatars: set[str] = set()
    if room.word is not None:
        room.current_word_id = room.word.get("id")
        hint_pool = room.word.get("hint_pool") or []
        if not room.selected_hint or room.selected_hint not in (hint_pool or [room.word.get("hint")]):
            room.selected_hint = choose_hint_for_word(room.word)
        room.word["hint"] = room.selected_hint

    for player_data in snapshot.get("players", []):
        stored_avatar = player_data.get("avatar")
        avatar = stored_avatar if stored_avatar in ALLOWED_AVATARS else ""
        if not avatar or avatar in used_avatars:
            available_avatars = [item for item in ALLOWED_AVATARS if item not in used_avatars]
            avatar = random.choice(available_avatars or ALLOWED_AVATARS)
        used_avatars.add(avatar)
        player = Player(
            id=player_data["id"],
            name=player_data["name"],
            avatar=avatar,
            is_host=bool(player_data.get("is_host", False)),
            connected=False,
            last_seen_at=float(player_data.get("last_seen_at", time.time())),
            connection_state=str(player_data.get("connection_state", "offline")),
            disconnect_started_at=player_data.get("disconnect_started_at"),
            viewed_secret=bool(player_data.get("viewed_secret", False)),
            confirmed=bool(player_data.get("confirmed", False)),
            requested_vote=bool(player_data.get("requested_vote", False)),
            has_voted=bool(player_data.get("has_voted", False)),
            disconnected_at=player_data.get("disconnected_at"),
            joined_at=float(player_data.get("joined_at", time.time())),
        )
        room.players[player.id] = player
    return room


def persist_room(room: Room) -> None:
    save_room_snapshot(room.code, room_to_snapshot(room))


def set_room_event(room: Room, event_type: str, player: Player) -> None:
    room.last_event = {
        "type": event_type,
        "player_id": player.id,
        "player_name": player.name,
        "player_avatar": player.avatar,
        "created_at": time.time(),
        "event_id": str(uuid.uuid4()),
    }


def ensure_scoreboard_player(room: Room, player_id: str) -> None:
    room.scoreboard.setdefault(player_id, {"discoveries": 0, "survivals": 0})


def update_scoreboard(room: Room) -> None:
    if room.varalica_id is None:
        return
    for player_id in room.players:
        ensure_scoreboard_player(room, player_id)

    counts = vote_counts(room)
    top_player_ids = tied_top_player_ids(room)
    tie = len(top_player_ids) > 1
    players_found_varalica = not tie and bool(top_player_ids) and top_player_ids[0] == room.varalica_id
    if players_found_varalica:
        for voter_id, target_id in room.final_votes.items():
            if target_id == room.varalica_id and voter_id in room.scoreboard:
                room.scoreboard[voter_id]["discoveries"] += 1
    else:
        ensure_scoreboard_player(room, room.varalica_id)
        room.scoreboard[room.varalica_id]["survivals"] += 1


def cancel_empty_room_cleanup(room: Room) -> None:
    room.empty_since = None
    if room.empty_cleanup_task and not room.empty_cleanup_task.done():
        room.empty_cleanup_task.cancel()
    room.empty_cleanup_task = None


def schedule_empty_room_cleanup(room: Room) -> None:
    room.empty_since = time.time()
    stop_timer(room)
    if room.empty_cleanup_task and not room.empty_cleanup_task.done():
        room.empty_cleanup_task.cancel()
    room.empty_cleanup_task = asyncio.create_task(empty_room_cleanup_loop(room.code))


async def empty_room_cleanup_loop(room_code: str) -> None:
    await asyncio.sleep(EMPTY_ROOM_CLEANUP_SECONDS)
    room = rooms.get(room_code)
    if room is None or room.players:
        return
    stop_timer(room)
    delete_room_data(room_code)
    rooms.pop(room_code, None)


def normalize_discussion_seconds(value: int | None) -> int:
    if value in ALLOWED_DISCUSSION_SECONDS:
        return int(value)
    return DISCUSSION_SECONDS


def load_persisted_rooms() -> None:
    for room_code, snapshot in load_room_snapshots().items():
        try:
            rooms[room_code.upper()] = room_from_snapshot(snapshot)
        except (KeyError, TypeError, ValueError):
            continue


def choose_word(room: Room) -> dict:
    room.used_word_indexes = load_used_word_indexes(room.code)
    selected_words = words_for_category(room.selected_category)
    selected_ids = {word["id"] for word in selected_words}
    selected_indexes = [
        index
        for index, word in enumerate(STARTER_WORDS)
        if word["id"] in selected_ids
    ]
    used_selected_indexes = room.used_word_indexes.intersection(selected_indexes)
    if len(used_selected_indexes) >= len(selected_indexes):
        reset_selected_used_word_indexes(room.code, selected_indexes)
        room.used_word_indexes = room.used_word_indexes.difference(selected_indexes)

    available_indexes = list(set(selected_indexes) - room.used_word_indexes)
    if not available_indexes:
        reset_used_word_indexes(room.code)
        room.used_word_indexes.clear()
        available_indexes = list(range(len(STARTER_WORDS)))

    word_index = random.choice(available_indexes)
    room.used_word_indexes.add(word_index)
    save_used_word_index(room.code, word_index)
    selected_word = dict(STARTER_WORDS[word_index])
    selected_word["hint_pool"] = list(selected_word.get("hint_pool") or [])
    room.current_word_id = selected_word["id"]
    room.selected_hint = choose_hint_for_word(selected_word)
    selected_word["hint"] = room.selected_hint
    return selected_word


def choose_hint_for_word(word: dict) -> str:
    hint_pool = list(word.get("hint_pool") or [])
    if hint_pool:
        return random.choice(hint_pool)
    return word.get("hint", "Razmišljaj o kategoriji i slušaj kako drugi opisuju riječ.")


def selected_word_matches_room(room: Room) -> bool:
    return (
        room.word is not None
        and room.current_word_id is not None
        and room.word.get("id") == room.current_word_id
        and bool(room.selected_hint)
        and room.selected_hint in (room.word.get("hint_pool") or [room.word.get("hint")])
    )


def prepare_reveal_round(room: Room, active_players: list[Player]) -> None:
    for player in room.players.values():
        player.viewed_secret = False
        player.confirmed = False
        player.requested_vote = False
        player.has_voted = False

    room.state = "reveal"
    room.round_player_ids = [player.id for player in active_players]
    room.varalica_id = choose_varalica_id(room, room.round_player_ids)
    room.current_word_id = None
    room.selected_hint = None
    room.word = choose_word(room)
    room.discussion_started_at = None
    room.current_player_index = 0
    room.vote_request_player_ids.clear()
    room.final_votes.clear()
    room.overtime_started_at = None
    room.overtime_used = False
    stop_timer(room)


def choose_varalica_id(room: Room, active_player_ids: list[str]) -> str:
    if not active_player_ids:
        raise HTTPException(status_code=400, detail="Nema aktivnih igraca.")

    recent_limit = max(1, min(3, len(active_player_ids) - 1))
    recent_ids = [player_id for player_id in room.recent_varalica_ids[-recent_limit:] if player_id in active_player_ids]
    last_varalica_id = room.recent_varalica_ids[-1] if room.recent_varalica_ids else None
    candidates = [player_id for player_id in active_player_ids if player_id != last_varalica_id]
    if len(active_player_ids) == 1:
        candidates = list(active_player_ids)

    less_recent_candidates = [player_id for player_id in active_player_ids if player_id not in recent_ids]
    if len(less_recent_candidates) >= 2:
        candidates = less_recent_candidates
    if not candidates:
        candidates = list(active_player_ids)

    selected_id = secrets.choice(candidates)
    room.recent_varalica_ids.append(selected_id)
    room.recent_varalica_ids = [
        player_id
        for player_id in room.recent_varalica_ids[-10:]
        if player_id in room.players
    ]
    return selected_id


def reset_room_to_lobby(room: Room) -> None:
    stop_timer(room)
    cancel_empty_room_cleanup(room)
    room.state = "lobby"
    room.varalica_id = None
    room.word = None
    room.current_word_id = None
    room.selected_hint = None
    room.round_player_ids.clear()
    room.discussion_started_at = None
    room.current_player_index = 0
    room.vote_request_player_ids.clear()
    room.final_votes.clear()
    room.overtime_started_at = None
    room.overtime_used = False
    room.round_number = 1
    room.last_event = None
    room.kicked_player_ids.clear()
    room.scoreboard = {
        player_id: {"discoveries": 0, "survivals": 0}
        for player_id in room.players
    }
    for player in room.players.values():
        player.viewed_secret = False
        player.confirmed = False
        player.requested_vote = False
        player.has_voted = False


def is_player_active_for_round(player: Player) -> bool:
    return time.time() - player.last_seen_at <= REMOVE_AFTER_SECONDS


def player_connection_status(player: Player) -> str:
    elapsed = time.time() - player.last_seen_at
    if player.connected and elapsed <= ACTIVE_GRACE_SECONDS:
        player.connection_state = "active"
        return "active"
    if elapsed <= IDLE_AFTER_SECONDS:
        player.connection_state = "away"
        return "away"
    if elapsed <= REMOVE_AFTER_SECONDS:
        player.connection_state = "idle"
        return "idle"
    player.connection_state = "offline"
    return "offline"


def cleanup_expired_disconnected_players(room: Room) -> None:
    now = time.time()
    expired_ids = [
        player_id
        for player_id, player in room.players.items()
        if now - player.last_seen_at > REMOVE_AFTER_SECONDS
    ]
    for player_id in expired_ids:
        remove_player_from_room(room, player_id)
    if expired_ids:
        normalize_current_player(room)
    if expired_ids and not room.players:
        schedule_empty_room_cleanup(room)


def remove_player_from_room(room: Room, player_id: str) -> None:
    removed_player = room.players.get(player_id)
    removed_joined_at = removed_player.joined_at if removed_player else None
    room.players.pop(player_id, None)
    room.sockets.pop(player_id, None)
    room.scoreboard.pop(player_id, None)
    if player_id in room.round_player_ids:
        room.round_player_ids.remove(player_id)
    room.vote_request_player_ids.discard(player_id)
    room.final_votes.pop(player_id, None)
    for voter_id, target_id in list(room.final_votes.items()):
        if target_id == player_id:
            room.final_votes.pop(voter_id, None)
            if voter_id in room.players:
                room.players[voter_id].has_voted = False
    if player_id == room.host_id:
        assign_new_host(room, removed_joined_at)
    normalize_current_player(room)


def assign_new_host(room: Room, after_joined_at: float | None = None) -> None:
    room.host_id = None
    for player in room.players.values():
        player.is_host = False
    eligible_players = sorted(
        [player for player in room.players.values() if player.id not in room.kicked_player_ids],
        key=lambda player: player.joined_at,
    )
    if not eligible_players:
        return
    if after_joined_at is not None:
        for player in eligible_players:
            if player.joined_at > after_joined_at:
                set_host(room, player.id)
                return
    set_host(room, eligible_players[0].id)


def set_host(room: Room, player_id: str) -> None:
    for player in room.players.values():
        player.is_host = player.id == player_id
    room.host_id = player_id if player_id in room.players else None


async def reconcile_after_player_removed(room: Room) -> None:
    normalize_current_player(room)
    if room.state == "reveal" and all_active_players_confirmed(room):
        await enter_discussion(room)
        return
    if room.state == "discussion" and all_active_players_requested_vote(room):
        room.state = "ready_for_final_voting"
        stop_timer(room)
        return
    if room.state in {"final_voting", "overtime_voting"} and all_active_players_voted(room):
        finish_voting(room)
        return
    if room.state == "voting_complete" and not all_active_players_voted(room):
        room.state = "final_voting" if not room.overtime_used else "overtime_voting"
        return


def room_lifecycle(room: Room) -> str:
    if room.code not in rooms:
        return "deleted"
    if not room.players:
        return "idle" if room.empty_since is not None else "expired"
    if all(player_connection_status(player) == "offline" for player in room.players.values()):
        return "expired"
    return "active"


def active_round_player_ids(room: Room) -> list[str]:
    cleanup_expired_disconnected_players(room)
    return [
        player_id
        for player_id in room.round_player_ids
        if player_id in room.players and is_player_active_for_round(room.players[player_id])
    ]


def all_active_players_confirmed(room: Room) -> bool:
    active_ids = active_round_player_ids(room)
    return bool(active_ids) and all(room.players[player_id].confirmed for player_id in active_ids)


def all_active_players_requested_vote(room: Room) -> bool:
    active_ids = active_round_player_ids(room)
    return bool(active_ids) and all(player_id in room.vote_request_player_ids for player_id in active_ids)


def all_active_players_voted(room: Room) -> bool:
    active_ids = active_round_player_ids(room)
    return bool(active_ids) and all(player_id in room.final_votes for player_id in active_ids)


def vote_target_for_player(room: Room, player_id: str) -> dict | None:
    target_id = room.final_votes.get(player_id)
    if target_id is None or target_id not in room.players:
        return None
    return {
        "id": target_id,
        "name": room.players[target_id].name,
        "avatar": room.players[target_id].avatar,
    }


def vote_counts(room: Room) -> dict[str, int]:
    counts = {player_id: 0 for player_id in room.round_player_ids if player_id in room.players}
    for target_id in room.final_votes.values():
        if target_id in counts:
            counts[target_id] += 1
    return counts


def tied_top_player_ids(room: Room) -> list[str]:
    counts = vote_counts(room)
    highest_vote_count = max(counts.values(), default=0)
    return [
        player_id
        for player_id, count in counts.items()
        if count == highest_vote_count
    ]


def is_vote_tied(room: Room) -> bool:
    return len(tied_top_player_ids(room)) > 1


def finish_voting(room: Room) -> None:
    room.state = "voting_complete"
    stop_timer(room)


def enter_discussion_values(room: Room) -> None:
    room.state = "discussion"
    room.discussion_started_at = time.time()
    room.current_player_index = 0
    room.vote_request_player_ids.clear()
    room.final_votes.clear()
    for player in room.players.values():
        player.requested_vote = False
        player.has_voted = False
    normalize_current_player(room)


async def enter_discussion(room: Room) -> None:
    if room.state != "reveal":
        return
    enter_discussion_values(room)
    stop_timer(room)
    room.timer_task = asyncio.create_task(timer_loop(room.code))
    persist_room(room)
    await broadcast_room(room)


async def timer_loop(room_code: str) -> None:
    while True:
        await asyncio.sleep(1)
        room = rooms.get(room_code)
        if room is None:
            return
        if room.state == "discussion":
            await broadcast_room(room)
            continue
        if room.state == "overtime" and room.overtime_started_at is not None:
            if overtime_remaining(room) == 0:
                room.state = "overtime_voting"
                room.overtime_started_at = None
                room.final_votes.clear()
                for player in room.players.values():
                    player.has_voted = False
                room.timer_task = None
                persist_room(room)
            await broadcast_room(room)
            continue
        cleanup_expired_disconnected_players(room)
        return


async def disconnected_player_status_loop(room_code: str, player_id: str) -> None:
    checkpoints = [AWAY_AFTER_SECONDS, IDLE_AFTER_SECONDS, REMOVE_AFTER_SECONDS]
    started_at = time.time()
    for checkpoint in checkpoints:
        await asyncio.sleep(max(0, checkpoint - (time.time() - started_at)))
        room = rooms.get(room_code)
        if room is None:
            return
        player = room.players.get(player_id)
        if player is None or time.time() - player.last_seen_at < checkpoint:
            return
        cleanup_expired_disconnected_players(room)
        persist_room(room)
        await broadcast_room(room)


async def presence_monitor_loop() -> None:
    while True:
        await asyncio.sleep(10)
        for room in list(rooms.values()):
            before_ids = set(room.players)
            cleanup_expired_disconnected_players(room)
            if before_ids != set(room.players):
                persist_room(room)
                await broadcast_room(room)
                continue
            if room.players:
                await broadcast_room(room)


def stop_timer(room: Room) -> None:
    if room.timer_task and not room.timer_task.done():
        room.timer_task.cancel()
    room.timer_task = None


def discussion_remaining(room: Room) -> int:
    if room.discussion_started_at is None:
        return room.discussion_duration_seconds
    elapsed = max(0, int(time.time() - room.discussion_started_at))
    return max(0, room.discussion_duration_seconds - elapsed)


def voting_seconds_left(room: Room) -> int:
    if room.discussion_started_at is None:
        return VOTING_LOCK_SECONDS
    elapsed = max(0, int(time.time() - room.discussion_started_at))
    return max(0, VOTING_LOCK_SECONDS - elapsed)


def voting_unlocked(room: Room) -> bool:
    return voting_seconds_left(room) == 0


def overtime_remaining(room: Room) -> int:
    if room.overtime_started_at is None:
        return OVERTIME_SECONDS
    elapsed = max(0, int(time.time() - room.overtime_started_at))
    return max(0, OVERTIME_SECONDS - elapsed)


def current_player_id(room: Room) -> str | None:
    if not room.round_player_ids:
        return None
    if room.current_player_index < 0 or room.current_player_index >= len(room.round_player_ids):
        room.current_player_index = 0
    return room.round_player_ids[room.current_player_index]


def normalize_current_player(room: Room) -> None:
    active_ids = active_round_player_ids(room)
    if not active_ids:
        room.current_player_index = 0
        return
    current_id = current_player_id(room)
    if current_id not in active_ids:
        room.current_player_index = room.round_player_ids.index(active_ids[0])


def public_state(room: Room, viewer_id: str) -> dict:
    cleanup_expired_disconnected_players(room)
    normalize_current_player(room)
    all_confirmed = room.state == "reveal" and all_active_players_confirmed(room)
    return {
        "room_code": room.code,
        "state": room.state,
        "viewer_id": viewer_id,
        "host_id": room.host_id,
        "min_players": MIN_PLAYERS,
        "max_players": MAX_PLAYERS,
        "idle_after_seconds": IDLE_AFTER_SECONDS,
        "away_after_seconds": AWAY_AFTER_SECONDS,
        "remove_after_seconds": REMOVE_AFTER_SECONDS,
        "reconnect_grace_seconds": RECONNECT_GRACE_SECONDS,
        "lifecycle": room_lifecycle(room),
        "categories": ALLOWED_CATEGORIES,
        "selected_category": room.selected_category,
        "discussion_duration_seconds": room.discussion_duration_seconds,
        "allowed_discussion_seconds": sorted(ALLOWED_DISCUSSION_SECONDS),
        "round_number": room.round_number,
        "scoreboard": scoreboard_state(room),
        "last_event": room.last_event,
        "player_count": len(room.players),
        "not_enough_players_message": "Nema dovoljno igraca za nastavak igre." if 0 < len(active_round_player_ids(room)) < MIN_PLAYERS and room.state != "lobby" else "",
        "all_confirmed": all_confirmed,
        "discussion": discussion_state(room),
        "overtime": overtime_state(room),
        "voting_complete": voting_complete_state(room),
        "results": results_state(room),
        "players": [
            {
                "id": player.id,
                "name": player.name,
                "avatar": player.avatar,
                "is_host": player.is_host,
                "connected": player.connected,
                "connection_status": player_connection_status(player),
                "viewed_secret": player.viewed_secret if room.state == "reveal" else False,
                "confirmed": player.confirmed if room.state == "reveal" else False,
                "is_current": player.id == current_player_id(room) if room.state in {"discussion", "overtime"} else False,
                "requested_vote": player.id in room.vote_request_player_ids,
                "has_voted": player.id in room.final_votes if room.state in {"final_voting", "overtime_voting", "voting_complete", "results"} else False,
                "is_active_round_player": player.id in active_round_player_ids(room),
                "temporarily_disconnected": player_connection_status(player) in {"away", "idle"},
                "vote_target": vote_target_for_player(room, player.id),
            }
            for player in room.players.values()
        ],
        "private": private_state(room, viewer_id),
    }


def discussion_state(room: Room) -> dict | None:
    if room.state not in {"discussion", "ready_for_final_voting"}:
        return None
    return {
        "duration_seconds": room.discussion_duration_seconds,
        "remaining_seconds": discussion_remaining(room),
        "voting_locked_seconds": VOTING_LOCK_SECONDS,
        "voting_seconds_left": voting_seconds_left(room),
        "voting_unlocked": voting_unlocked(room),
        "current_player_id": current_player_id(room),
        "requested_vote_count": len(room.vote_request_player_ids),
        "active_player_count": len(active_round_player_ids(room)),
    }


def overtime_state(room: Room) -> dict | None:
    if room.state not in {"overtime", "overtime_voting"}:
        return None
    return {
        "duration_seconds": OVERTIME_SECONDS,
        "remaining_seconds": overtime_remaining(room),
        "started": room.overtime_started_at is not None,
        "used": room.overtime_used,
        "current_player_id": current_player_id(room),
        "active_player_count": len(active_round_player_ids(room)),
    }


def voting_complete_state(room: Room) -> dict | None:
    if room.state != "voting_complete":
        return None
    return {
        "is_tie": is_vote_tied(room),
        "can_overtime": is_vote_tied(room) and not room.overtime_used,
        "overtime_used": room.overtime_used,
        "active_player_count": len(active_round_player_ids(room)),
        "voted_count": len([player_id for player_id in active_round_player_ids(room) if player_id in room.final_votes]),
    }


def scoreboard_state(room: Room) -> list[dict]:
    rows: list[dict] = []
    for player_id, stats in room.scoreboard.items():
        player = room.players.get(player_id)
        if player is None:
            continue
        rows.append(
            {
                "player_id": player_id,
                "name": player.name,
                "avatar": player.avatar,
                "discoveries": int(stats.get("discoveries", 0)),
                "survivals": int(stats.get("survivals", 0)),
            }
        )
    return rows


def results_state(room: Room) -> dict | None:
    if room.state != "results" or room.word is None or room.varalica_id is None:
        return None

    active_ids = active_round_player_ids(room)
    counts = vote_counts(room)
    top_player_ids = tied_top_player_ids(room)
    tie = len(top_player_ids) > 1

    if tie and room.overtime_used:
        outcome = "Nakon produžetka glasanje je i dalje neriješeno. Varalica je preživjela."
    elif tie:
        outcome = "Glasanje je neriješeno. Varalica je preživjela."
    elif not tie and top_player_ids and top_player_ids[0] == room.varalica_id:
        outcome = "Igrači su pronašli Varalicu."
    else:
        outcome = "Varalica je pobijedila."
    was_varalica_caught = not tie and bool(top_player_ids) and top_player_ids[0] == room.varalica_id

    return {
        "varalica": {
            "id": room.varalica_id,
            "name": room.players[room.varalica_id].name,
            "avatar": room.players[room.varalica_id].avatar,
        },
        "word": {
            "hr": room.word["hr"],
            "sr": room.word["sr"],
            "category": room.word["category"],
        },
        "outcome": outcome,
        "is_tie": tie,
        "was_varalica_caught": was_varalica_caught,
        "active_player_count": len(active_ids),
        "vote_summary": [
            {
                "player_id": player_id,
                "name": room.players[player_id].name,
                "avatar": room.players[player_id].avatar,
                "votes": counts.get(player_id, 0),
            }
            for player_id in room.round_player_ids
            if player_id in room.players
        ],
        "individual_votes": [
            {
                "voter_id": voter_id,
                "voter_name": room.players[voter_id].name,
                "voter_avatar": room.players[voter_id].avatar,
                "target_id": target_id,
                "target_name": room.players[target_id].name,
                "target_avatar": room.players[target_id].avatar,
            }
            for voter_id, target_id in room.final_votes.items()
            if voter_id in room.players and target_id in room.players
        ],
        "correct_guessers": [
            {
                "player_id": voter_id,
                "name": room.players[voter_id].name,
                "avatar": room.players[voter_id].avatar,
            }
            for voter_id, target_id in room.final_votes.items()
            if target_id == room.varalica_id and voter_id in room.players
        ],
    }


def private_state(room: Room, viewer_id: str) -> dict | None:
    if room.state != "reveal" or viewer_id not in room.round_player_ids:
        return None
    if viewer_id == room.varalica_id:
        if room.word is None:
            return {"role": "varalica", "message": "Ti si Varalica"}
        if not selected_word_matches_room(room):
            raise HTTPException(status_code=500, detail="Runda nema usklađenu riječ i hint.")
        return {
            "role": "varalica",
            "message": "Ti si Varalica",
            "hint": room.selected_hint,
            "word_id": room.current_word_id,
            "category": room.word["category"],
        }
    if room.word is None:
        return None
    if not selected_word_matches_room(room):
        raise HTTPException(status_code=500, detail="Runda nema usklađenu riječ i hint.")
    return {
        "role": "player",
        "word": {
            "id": room.current_word_id,
            "hr": room.word["hr"],
            "sr": room.word["sr"],
            "category": room.word["category"],
        },
    }


async def broadcast_room(room: Room) -> None:
    stale_player_ids: list[str] = []
    for player_id, socket in list(room.sockets.items()):
        try:
            await socket.send_json(public_state(room, player_id))
        except RuntimeError:
            stale_player_ids.append(player_id)

    for player_id in stale_player_ids:
        room.sockets.pop(player_id, None)
