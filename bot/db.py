from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta
from typing import Any

import aiosqlite

from .config import DB_PATH
from .utils import fmt_dt

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    full_name   TEXT,
    first_seen  TEXT NOT NULL,
    last_seen   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    username    TEXT,
    full_name   TEXT,
    guest_name  TEXT,
    rating      INTEGER NOT NULL,
    text        TEXT,
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reviews_created ON reviews(created_at);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def upsert_user(
    user_id: int,
    username: str | None,
    full_name: str | None,
) -> None:
    now = _now()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, full_name, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username  = excluded.username,
                full_name = excluded.full_name,
                last_seen = excluded.last_seen
            """,
            (user_id, username, full_name, now, now),
        )
        await db.commit()


async def add_review(
    user_id: int,
    username: str | None,
    full_name: str | None,
    guest_name: str | None,
    rating: int,
    text: str | None,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO reviews
                (user_id, username, full_name, guest_name, rating, text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, full_name, guest_name, rating, text, _now()),
        )
        await db.commit()
        return int(cursor.lastrowid or 0)


async def get_reviews(limit: int = 5, offset: int = 0) -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reviews ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ) as cursor:
            return [dict(row) async for row in cursor]


async def get_user_reviews(user_id: int, limit: int = 5) -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reviews WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ) as cursor:
            return [dict(row) async for row in cursor]


async def get_all_reviews() -> list[dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM reviews ORDER BY id") as cursor:
            return [dict(row) async for row in cursor]


async def count_reviews() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM reviews") as cursor:
            row = await cursor.fetchone()
            return int(row[0]) if row else 0


async def get_stats() -> dict[str, Any]:
    now = datetime.now()
    week_ago = (now - timedelta(days=7)).isoformat(timespec="seconds")
    today = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(
        timespec="seconds"
    )

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT COUNT(*) AS total, COALESCE(AVG(rating), 0) AS avg FROM reviews"
        ) as cursor:
            row = await cursor.fetchone()
        total = int(row["total"]) if row else 0
        avg = float(row["avg"]) if row else 0.0

        async with db.execute(
            "SELECT COUNT(*) AS c FROM reviews WHERE created_at >= ?", (week_ago,)
        ) as cursor:
            row = await cursor.fetchone()
        week = int(row["c"]) if row else 0

        async with db.execute(
            "SELECT COUNT(*) AS c FROM reviews WHERE created_at >= ?", (today,)
        ) as cursor:
            row = await cursor.fetchone()
        today_count = int(row["c"]) if row else 0

        by_rating = {i: 0 for i in range(1, 6)}
        async with db.execute(
            "SELECT rating, COUNT(*) AS c FROM reviews GROUP BY rating"
        ) as cursor:
            async for row in cursor:
                by_rating[int(row["rating"])] = int(row["c"])

    return {
        "total": total,
        "avg": avg,
        "week": week,
        "today": today_count,
        "by_rating": by_rating,
    }


async def export_csv() -> bytes:
    reviews = await get_all_reviews()
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\r\n")
    writer.writerow(
        [
            "ID",
            "Дата",
            "Оценка",
            "Имя гостя",
            "Отзыв",
            "Telegram",
            "Username",
            "User ID",
        ]
    )
    for review in reviews:
        writer.writerow(
            [
                review["id"],
                fmt_dt(review["created_at"]),
                review["rating"],
                review.get("guest_name") or review.get("full_name") or "",
                (review.get("text") or "").replace("\n", " "),
                review.get("full_name") or "",
                f"@{review['username']}" if review.get("username") else "",
                review["user_id"],
            ]
        )
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


async def get_setting(key: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def set_setting(key: str, value: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        await db.commit()


async def delete_setting(key: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM settings WHERE key = ?", (key,))
        await db.commit()
