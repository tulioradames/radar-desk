"""Persistência de usuários locais e auditoria."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from radar_desk.data.database import Database
from radar_desk.models.user import AuditEntry, User


class AuthRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def count_users(self) -> int:
        with self.database.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()
        return int(row["total"])

    def create_user(
        self,
        username: str,
        display_name: str,
        role: str,
        password_hash: str,
        password_salt: str,
        now: datetime,
    ) -> User:
        timestamp = now.isoformat(timespec="seconds")
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    username, display_name, role, password_hash, password_salt,
                    active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (username, display_name, role, password_hash, password_salt, timestamp, timestamp),
            )
            row = connection.execute(
                "SELECT * FROM users WHERE id = ?", (int(cursor.lastrowid),)
            ).fetchone()
        return self._user_from_row(row)

    def credentials_for(self, username: str) -> sqlite3.Row | None:
        with self.database.connect() as connection:
            return connection.execute(
                "SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,)
            ).fetchone()

    def list_users(self) -> list[User]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM users ORDER BY display_name, username"
            ).fetchall()
        return [self._user_from_row(row) for row in rows]

    def set_active(self, user_id: int, active: bool, now: datetime) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "UPDATE users SET active = ?, updated_at = ? WHERE id = ?",
                (int(active), now.isoformat(timespec="seconds"), user_id),
            )

    def add_audit(
        self,
        user: User | None,
        action: str,
        entity_type: str,
        entity_id: str,
        details: str,
        now: datetime,
    ) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_log (
                    user_id, username, action, entity_type, entity_id, details, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id if user else None,
                    user.username if user else "sistema",
                    action,
                    entity_type,
                    entity_id,
                    details,
                    now.isoformat(timespec="seconds"),
                ),
            )

    def list_audit(self, limit: int = 200) -> list[AuditEntry]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM audit_log ORDER BY created_at DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            AuditEntry(
                id=int(row["id"]),
                user_id=int(row["user_id"]) if row["user_id"] is not None else None,
                username=str(row["username"]),
                action=str(row["action"]),
                entity_type=str(row["entity_type"]),
                entity_id=str(row["entity_id"]),
                details=str(row["details"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    @staticmethod
    def _user_from_row(row: sqlite3.Row) -> User:
        return User(
            id=int(row["id"]),
            username=str(row["username"]),
            display_name=str(row["display_name"]),
            role=str(row["role"]),
            active=bool(row["active"]),
            created_at=str(row["created_at"]),
        )
