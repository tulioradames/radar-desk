"""Inicialização e acesso seguro ao banco SQLite local."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = 2


class Database:
    """Pequena camada de infraestrutura para conexões SQLite."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_info (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    version INTEGER NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                INSERT INTO schema_info (id, version)
                VALUES (1, 1)
                ON CONFLICT(id) DO NOTHING;

                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            current_version = int(
                connection.execute(
                    "SELECT version FROM schema_info WHERE id = 1"
                ).fetchone()["version"]
            )
            if current_version < 2:
                self._migrate_to_v2(connection)

    @staticmethod
    def _migrate_to_v2(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tickets_updated_at
                ON tickets(updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_tickets_status
                ON tickets(status);

            CREATE TABLE IF NOT EXISTS protocol_sequences (
                year INTEGER PRIMARY KEY,
                last_number INTEGER NOT NULL CHECK (last_number > 0)
            );

            UPDATE schema_info
            SET version = 2, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1;
            """
        )

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def health_check(self) -> bool:
        try:
            with self.connect() as connection:
                result = connection.execute("SELECT 1").fetchone()
            return bool(result and result[0] == 1)
        except sqlite3.Error:
            return False

    def schema_version(self) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT version FROM schema_info WHERE id = 1"
            ).fetchone()
        return int(row["version"]) if row else 0
