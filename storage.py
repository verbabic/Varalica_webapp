from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("VARALICA_DB_PATH", BASE_DIR / "varalica.sqlite3"))


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_storage() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                room_code TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS room_used_words (
                room_code TEXT NOT NULL,
                word_index INTEGER NOT NULL,
                used_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (room_code, word_index)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                message TEXT NOT NULL,
                email TEXT,
                ui_language TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )


def load_used_word_indexes(room_code: str) -> set[int]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT word_index FROM room_used_words WHERE room_code = ?",
            (room_code,),
        ).fetchall()
    return {int(row[0]) for row in rows}


def save_used_word_index(room_code: str, word_index: int) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO room_used_words (room_code, word_index)
            VALUES (?, ?)
            """,
            (room_code, word_index),
        )


def reset_used_word_indexes(room_code: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM room_used_words WHERE room_code = ?",
            (room_code,),
        )


def reset_selected_used_word_indexes(room_code: str, word_indexes: list[int]) -> None:
    if not word_indexes:
        return
    placeholders = ",".join("?" for _ in word_indexes)
    with get_connection() as connection:
        connection.execute(
            f"DELETE FROM room_used_words WHERE room_code = ? AND word_index IN ({placeholders})",
            (room_code, *word_indexes),
        )


def save_room_snapshot(room_code: str, state: dict) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO rooms (room_code, state_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(room_code) DO UPDATE SET
                state_json = excluded.state_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (room_code, json.dumps(state, ensure_ascii=False)),
        )


def delete_room_data(room_code: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM rooms WHERE room_code = ?", (room_code,))
        connection.execute("DELETE FROM room_used_words WHERE room_code = ?", (room_code,))


def find_recent_feedback(category: str, message: str, email: str | None, since: str) -> int | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id FROM feedback
            WHERE category = ?
              AND message = ?
              AND IFNULL(email, '') = ?
              AND created_at >= ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (category, message, email or "", since),
        ).fetchone()
    if row is None:
        return None
    return int(row[0])


def insert_feedback(category: str, message: str, email: str | None, ui_language: str, created_at: str) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO feedback (category, message, email, ui_language, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (category, message, email, ui_language, created_at),
        )
        return int(cursor.lastrowid)


def load_room_snapshots() -> dict[str, dict]:
    with get_connection() as connection:
        rows = connection.execute("SELECT room_code, state_json FROM rooms").fetchall()

    snapshots: dict[str, dict] = {}
    for room_code, state_json in rows:
        snapshots[str(room_code)] = json.loads(str(state_json))
    return snapshots
