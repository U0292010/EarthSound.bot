import json
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SQLiteRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    @asynccontextmanager
    async def _connection(self) -> AsyncIterator[aiosqlite.Connection]:
        connection = await aiosqlite.connect(self.database_path)
        connection.row_factory = aiosqlite.Row
        await connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
        finally:
            await connection.close()

    async def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        async with self._connection() as connection:
            await connection.execute("PRAGMA journal_mode = WAL")
            await connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS selections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL REFERENCES users(telegram_id),
                    dataset_key TEXT NOT NULL,
                    location_key TEXT NOT NULL,
                    start_year INTEGER,
                    end_year INTEGER,
                    source TEXT NOT NULL,
                    selected_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS generated_audio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL REFERENCES users(telegram_id),
                    dataset_key TEXT NOT NULL,
                    location_key TEXT NOT NULL,
                    start_year INTEGER,
                    end_year INTEGER,
                    file_name TEXT NOT NULL,
                    mime_type TEXT NOT NULL DEFAULT 'audio/mpeg',
                    audio_blob BLOB NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS activity_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL REFERENCES users(telegram_id),
                    activity_type TEXT NOT NULL,
                    dataset_key TEXT,
                    location_key TEXT,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS achievements (
                    achievement_key TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    target_count INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS user_achievements (
                    telegram_id INTEGER NOT NULL REFERENCES users(telegram_id),
                    achievement_key TEXT NOT NULL REFERENCES achievements(achievement_key),
                    progress INTEGER NOT NULL DEFAULT 0,
                    unlocked_at TEXT,
                    PRIMARY KEY (telegram_id, achievement_key)
                );

                CREATE INDEX IF NOT EXISTS idx_activity_user_created
                    ON activity_history(telegram_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_audio_user_created
                    ON generated_audio(telegram_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_selections_user
                    ON selections(telegram_id, dataset_key, location_key);
                """
            )
            await connection.commit()

    async def seed_achievements(self, definitions: Sequence[Any]) -> None:
        async with self._connection() as connection:
            await connection.executemany(
                """
                INSERT INTO achievements(achievement_key, title, description, target_count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(achievement_key) DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description,
                    target_count = excluded.target_count
                """,
                [
                    (
                        item.achievement_key,
                        item.title,
                        item.description,
                        item.target_count,
                    )
                    for item in definitions
                ],
            )
            await connection.commit()

    async def _upsert_user(self, connection: aiosqlite.Connection, user: Any) -> None:
        now = _utc_now()
        await connection.execute(
            """
            INSERT INTO users(telegram_id, username, first_name, last_name, created_at, last_seen_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                last_seen_at = excluded.last_seen_at
            """,
            (
                int(user.id),
                getattr(user, "username", None),
                getattr(user, "first_name", None),
                getattr(user, "last_name", None),
                now,
                now,
            ),
        )

    async def log_activity(
        self,
        user: Any,
        activity_type: str,
        dataset_key: str | None = None,
        location_key: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        async with self._connection() as connection:
            await self._upsert_user(connection, user)
            await connection.execute(
                """
                INSERT INTO activity_history(
                    telegram_id, activity_type, dataset_key, location_key, details_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user.id),
                    activity_type,
                    dataset_key,
                    location_key,
                    json.dumps(details or {}, ensure_ascii=True),
                    _utc_now(),
                ),
            )
            await connection.commit()

    async def save_selection(
        self,
        user: Any,
        dataset_key: str,
        location_key: str,
        source: str,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> None:
        async with self._connection() as connection:
            await self._upsert_user(connection, user)
            await connection.execute(
                """
                INSERT INTO selections(
                    telegram_id, dataset_key, location_key, start_year, end_year, source, selected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user.id),
                    dataset_key,
                    location_key,
                    start_year,
                    end_year,
                    source,
                    _utc_now(),
                ),
            )
            await connection.execute(
                """
                INSERT INTO activity_history(
                    telegram_id, activity_type, dataset_key, location_key, details_json, created_at
                ) VALUES (?, 'dataset_selected', ?, ?, ?, ?)
                """,
                (
                    int(user.id),
                    dataset_key,
                    location_key,
                    json.dumps(
                        {"start_year": start_year, "end_year": end_year, "source": source},
                        ensure_ascii=True,
                    ),
                    _utc_now(),
                ),
            )
            await connection.commit()

    async def save_generated_audio(
        self,
        user: Any,
        dataset_key: str,
        location_key: str,
        file_name: str,
        audio_data: bytes,
        source: str,
        start_year: int | None = None,
        end_year: int | None = None,
    ) -> None:
        async with self._connection() as connection:
            await self._upsert_user(connection, user)
            await connection.execute(
                """
                INSERT INTO generated_audio(
                    telegram_id, dataset_key, location_key, start_year, end_year,
                    file_name, audio_blob, source, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user.id),
                    dataset_key,
                    location_key,
                    start_year,
                    end_year,
                    file_name,
                    audio_data,
                    source,
                    _utc_now(),
                ),
            )
            await connection.execute(
                """
                INSERT INTO activity_history(
                    telegram_id, activity_type, dataset_key, location_key, details_json, created_at
                ) VALUES (?, 'audio_generated', ?, ?, ?, ?)
                """,
                (
                    int(user.id),
                    dataset_key,
                    location_key,
                    json.dumps(
                        {
                            "file_name": file_name,
                            "size_bytes": len(audio_data),
                            "start_year": start_year,
                            "end_year": end_year,
                            "source": source,
                        },
                        ensure_ascii=True,
                    ),
                    _utc_now(),
                ),
            )
            await connection.commit()

    async def get_achievement_statistics(self, telegram_id: int) -> dict[str, int]:
        async with self._connection() as connection:
            cursor = await connection.execute(
                """
                SELECT COUNT(DISTINCT dataset_key) AS datasets,
                       COUNT(DISTINCT location_key) AS locations
                FROM selections WHERE telegram_id = ?
                """,
                (telegram_id,),
            )
            selections = await cursor.fetchone()
            cursor = await connection.execute(
                "SELECT COUNT(*) AS total FROM generated_audio WHERE telegram_id = ?",
                (telegram_id,),
            )
            audios = await cursor.fetchone()
            cursor = await connection.execute(
                """
                SELECT COUNT(DISTINCT dataset_key) AS total
                FROM generated_audio
                WHERE telegram_id = ?
                  AND dataset_key IN ('temperature', 'sea_level', 'cloud_coverage')
                """,
                (telegram_id,),
            )
            climate = await cursor.fetchone()
        return {
            "datasets": int(selections["datasets"]),
            "locations": int(selections["locations"]),
            "audios": int(audios["total"]),
            "climate_audios": int(climate["total"]),
        }

    async def update_achievement_progress(
        self,
        telegram_id: int,
        achievement_key: str,
        progress: int,
        unlocked: bool,
    ) -> bool:
        async with self._connection() as connection:
            cursor = await connection.execute(
                """
                SELECT unlocked_at FROM user_achievements
                WHERE telegram_id = ? AND achievement_key = ?
                """,
                (telegram_id, achievement_key),
            )
            existing = await cursor.fetchone()
            already_unlocked = existing is not None and existing["unlocked_at"] is not None
            unlocked_at = _utc_now() if unlocked and not already_unlocked else (
                existing["unlocked_at"] if already_unlocked else None
            )
            await connection.execute(
                """
                INSERT INTO user_achievements(telegram_id, achievement_key, progress, unlocked_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_id, achievement_key) DO UPDATE SET
                    progress = excluded.progress,
                    unlocked_at = COALESCE(user_achievements.unlocked_at, excluded.unlocked_at)
                """,
                (telegram_id, achievement_key, progress, unlocked_at),
            )
            await connection.commit()
        return unlocked and not already_unlocked

    async def get_achievements(self, telegram_id: int) -> list[aiosqlite.Row]:
        async with self._connection() as connection:
            cursor = await connection.execute(
                """
                SELECT a.achievement_key, a.title, a.description, a.target_count,
                       COALESCE(ua.progress, 0) AS progress, ua.unlocked_at
                FROM achievements AS a
                LEFT JOIN user_achievements AS ua
                  ON ua.achievement_key = a.achievement_key AND ua.telegram_id = ?
                ORDER BY a.achievement_key
                """,
                (telegram_id,),
            )
            return await cursor.fetchall()

    async def get_recent_activity(self, telegram_id: int, limit: int = 10) -> list[aiosqlite.Row]:
        async with self._connection() as connection:
            cursor = await connection.execute(
                """
                SELECT activity_type, dataset_key, location_key, details_json, created_at
                FROM activity_history
                WHERE telegram_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (telegram_id, limit),
            )
            return await cursor.fetchall()