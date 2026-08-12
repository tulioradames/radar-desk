"""Inicialização e acesso seguro ao banco SQLite local."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = 5


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
                current_version = 2
            if current_version < 3:
                self._migrate_to_v3(connection)
                current_version = 3
            if current_version < 4:
                self._migrate_to_v4(connection)
                current_version = 4
            if current_version < 5:
                self._migrate_to_v5(connection)

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

    @staticmethod
    def _migrate_to_v3(connection: sqlite3.Connection) -> None:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(tickets)").fetchall()
        }
        if "assignee" not in columns:
            connection.execute(
                "ALTER TABLE tickets ADD COLUMN assignee TEXT NOT NULL DEFAULT ''"
            )
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS ticket_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                field_name TEXT NOT NULL DEFAULT '',
                old_value TEXT NOT NULL DEFAULT '',
                new_value TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_ticket_history_ticket
                ON ticket_history(ticket_id, created_at DESC, id DESC);

            CREATE TABLE IF NOT EXISTS ticket_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_ticket_comments_ticket
                ON ticket_comments(ticket_id, created_at DESC, id DESC);

            INSERT INTO ticket_history (
                ticket_id, action, field_name, old_value, new_value, created_at
            )
            SELECT id, 'Chamado importado', '', '', '', updated_at
            FROM tickets
            WHERE NOT EXISTS (
                SELECT 1 FROM ticket_history WHERE ticket_history.ticket_id = tickets.id
            );

            UPDATE schema_info
            SET version = 3, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1;
            """
        )

    @staticmethod
    def _migrate_to_v4(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS ticket_diagnostics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                data_json TEXT NOT NULL,
                report_path TEXT NOT NULL,
                screenshot_path TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_ticket_diagnostics_ticket
                ON ticket_diagnostics(ticket_id, created_at DESC, id DESC);

            UPDATE schema_info
            SET version = 4, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1;
            """
        )

    @staticmethod
    def _migrate_to_v5(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS ticket_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
                created_at TEXT NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_ticket_attachments_ticket
                ON ticket_attachments(ticket_id, created_at DESC, id DESC);

            UPDATE schema_info
            SET version = 5, updated_at = CURRENT_TIMESTAMP
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
