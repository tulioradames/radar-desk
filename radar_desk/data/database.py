"""Inicialização e acesso seguro ao banco SQLite local."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = 1


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
