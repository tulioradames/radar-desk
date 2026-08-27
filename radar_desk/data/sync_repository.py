"""Persistência e compactação da fila de sincronização."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

from radar_desk.data.database import Database
from radar_desk.models.sync import SyncEvent


class SyncRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def enqueue(
        self,
        entity_type: str,
        entity_id: str,
        operation: str,
        payload: dict,
        now: datetime,
    ) -> SyncEvent:
        timestamp = now.isoformat(timespec="seconds")
        with self.database.connect() as connection:
            previous = connection.execute(
                """
                SELECT * FROM sync_queue
                WHERE entity_type = ? AND entity_id = ? AND status = 'pending'
                ORDER BY id DESC LIMIT 1
                """,
                (entity_type, entity_id),
            ).fetchone()
            version = int(previous["local_version"]) + 1 if previous else 1
            if previous:
                connection.execute(
                    """
                    UPDATE sync_queue SET operation = ?, payload_json = ?,
                        local_version = ?, attempts = 0, last_error = '', updated_at = ?
                    WHERE id = ?
                    """,
                    (operation, json.dumps(payload, ensure_ascii=False), version, timestamp, int(previous["id"])),
                )
                event_id = int(previous["id"])
            else:
                cursor = connection.execute(
                    """
                    INSERT INTO sync_queue (
                        entity_type, entity_id, operation, payload_json, local_version,
                        status, attempts, last_error, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 'pending', 0, '', ?, ?)
                    """,
                    (entity_type, entity_id, operation, json.dumps(payload, ensure_ascii=False), version, timestamp, timestamp),
                )
                event_id = int(cursor.lastrowid)
            row = connection.execute(
                "SELECT * FROM sync_queue WHERE id = ?", (event_id,)
            ).fetchone()
        return self._from_row(row)

    def pending(self, limit: int = 100) -> list[SyncEvent]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM sync_queue WHERE status = 'pending'
                ORDER BY created_at, id LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def count_pending(self) -> int:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS total FROM sync_queue WHERE status = 'pending'"
            ).fetchone()
        return int(row["total"])

    def mark_done(self, event_id: int, now: datetime) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE sync_queue SET status = 'done', updated_at = ? WHERE id = ?",
                (now.isoformat(timespec="seconds"), event_id),
            )

    def mark_failed(self, event_id: int, error: str, now: datetime) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE sync_queue SET attempts = attempts + 1, last_error = ?,
                    updated_at = ? WHERE id = ?
                """,
                (error[:500], now.isoformat(timespec="seconds"), event_id),
            )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> SyncEvent:
        return SyncEvent(
            id=int(row["id"]), entity_type=str(row["entity_type"]),
            entity_id=str(row["entity_id"]), operation=str(row["operation"]),
            payload=json.loads(str(row["payload_json"])),
            local_version=int(row["local_version"]), status=str(row["status"]),
            attempts=int(row["attempts"]), last_error=str(row["last_error"]),
            created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
        )
