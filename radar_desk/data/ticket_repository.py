"""Persistência SQLite dos chamados e de suas interações."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from radar_desk.data.database import Database
from radar_desk.models.ticket import (
    Ticket,
    TicketComment,
    TicketFilter,
    TicketHistory,
    TicketInput,
)


class TicketNotFoundError(LookupError):
    pass


class TicketRepository:
    TRACKED_FIELDS = ("title", "description", "category", "priority", "status", "assignee")

    def __init__(self, database: Database) -> None:
        self.database = database

    def create(self, data: TicketInput, now: datetime) -> Ticket:
        timestamp = now.isoformat(timespec="seconds")
        with self.database.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            protocol = self._next_protocol(connection, now.year)
            cursor = connection.execute(
                """
                INSERT INTO tickets (
                    protocol, title, description, category, priority, status,
                    assignee, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    protocol,
                    data.title,
                    data.description,
                    data.category,
                    data.priority,
                    data.status,
                    data.assignee,
                    timestamp,
                    timestamp,
                ),
            )
            ticket_id = int(cursor.lastrowid)
            self._insert_history(
                connection, ticket_id, "Chamado criado", "", "", "", timestamp
            )
            row = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
        return self._from_row(row)

    @staticmethod
    def _next_protocol(connection: sqlite3.Connection, year: int) -> str:
        row = connection.execute(
            "SELECT last_number FROM protocol_sequences WHERE year = ?", (year,)
        ).fetchone()
        if row:
            number = int(row["last_number"]) + 1
            connection.execute(
                "UPDATE protocol_sequences SET last_number = ? WHERE year = ?",
                (number, year),
            )
        else:
            number = 1
            connection.execute(
                "INSERT INTO protocol_sequences (year, last_number) VALUES (?, ?)",
                (year, number),
            )
        return f"RD-{year}-{number:04d}"

    def update(self, ticket_id: int, data: TicketInput, now: datetime) -> Ticket:
        timestamp = now.isoformat(timespec="seconds")
        with self.database.connect() as connection:
            existing = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
            if not existing:
                raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")

            changes = [
                (field, str(existing[field]), str(getattr(data, field)))
                for field in self.TRACKED_FIELDS
                if str(existing[field]) != str(getattr(data, field))
            ]
            if not changes:
                return self._from_row(existing)

            connection.execute(
                """
                UPDATE tickets
                SET title = ?, description = ?, category = ?, priority = ?,
                    status = ?, assignee = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    data.title,
                    data.description,
                    data.category,
                    data.priority,
                    data.status,
                    data.assignee,
                    timestamp,
                    ticket_id,
                ),
            )
            for field, old_value, new_value in changes:
                self._insert_history(
                    connection,
                    ticket_id,
                    "Campo alterado",
                    field,
                    old_value,
                    new_value,
                    timestamp,
                )
            row = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
        return self._from_row(row)

    def reopen(self, ticket_id: int, now: datetime) -> Ticket:
        timestamp = now.isoformat(timespec="seconds")
        with self.database.connect() as connection:
            existing = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
            if not existing:
                raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")
            connection.execute(
                "UPDATE tickets SET status = 'Aberto', updated_at = ? WHERE id = ?",
                (timestamp, ticket_id),
            )
            self._insert_history(
                connection,
                ticket_id,
                "Chamado reaberto",
                "status",
                str(existing["status"]),
                "Aberto",
                timestamp,
            )
            row = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
        return self._from_row(row)

    def close_resolved(self, ticket_id: int, now: datetime) -> Ticket:
        timestamp = now.isoformat(timespec="seconds")
        with self.database.connect() as connection:
            existing = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
            if not existing:
                raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")
            connection.execute(
                "UPDATE tickets SET status = 'Encerrado', updated_at = ? WHERE id = ?",
                (timestamp, ticket_id),
            )
            self._insert_history(
                connection,
                ticket_id,
                "Chamado encerrado",
                "status",
                str(existing["status"]),
                "Encerrado",
                timestamp,
            )
            row = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
        return self._from_row(row)

    def delete(self, ticket_id: int) -> None:
        with self.database.connect() as connection:
            cursor = connection.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
            if cursor.rowcount == 0:
                raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")

    def get(self, ticket_id: int) -> Ticket:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
        if not row:
            raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")
        return self._from_row(row)

    def list_all(self) -> list[Ticket]:
        return self.list_filtered(TicketFilter())

    def list_filtered(self, filters: TicketFilter) -> list[Ticket]:
        conditions: list[str] = []
        parameters: list[str] = []
        search = filters.search.strip().lower()
        if search:
            pattern = f"%{search}%"
            columns = (
                "protocol",
                "title",
                "description",
                "category",
                "priority",
                "status",
                "assignee",
            )
            conditions.append(
                "(" + " OR ".join(f"LOWER({column}) LIKE ?" for column in columns) + ")"
            )
            parameters.extend([pattern] * len(columns))
        for column, value in (
            ("status", filters.status),
            ("priority", filters.priority),
            ("category", filters.category),
        ):
            if value:
                conditions.append(f"{column} = ?")
                parameters.append(value)
        if filters.start_date:
            conditions.append("substr(created_at, 1, 10) >= ?")
            parameters.append(filters.start_date)
        if filters.end_date:
            conditions.append("substr(created_at, 1, 10) <= ?")
            parameters.append(filters.end_date)

        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        with self.database.connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM tickets{where} ORDER BY updated_at DESC, id DESC",
                parameters,
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def add_comment(
        self,
        ticket_id: int,
        author: str,
        content: str,
        now: datetime,
    ) -> TicketComment:
        timestamp = now.isoformat(timespec="seconds")
        with self.database.connect() as connection:
            self._ensure_exists(connection, ticket_id)
            cursor = connection.execute(
                """
                INSERT INTO ticket_comments (ticket_id, author, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (ticket_id, author, content, timestamp),
            )
            comment_id = int(cursor.lastrowid)
            connection.execute(
                "UPDATE tickets SET updated_at = ? WHERE id = ?",
                (timestamp, ticket_id),
            )
            self._insert_history(
                connection,
                ticket_id,
                "Comentário adicionado",
                "comment",
                "",
                author,
                timestamp,
            )
            row = connection.execute(
                "SELECT * FROM ticket_comments WHERE id = ?", (comment_id,)
            ).fetchone()
        return self._comment_from_row(row)

    def get_comments(self, ticket_id: int) -> list[TicketComment]:
        with self.database.connect() as connection:
            self._ensure_exists(connection, ticket_id)
            rows = connection.execute(
                """
                SELECT * FROM ticket_comments
                WHERE ticket_id = ? ORDER BY created_at DESC, id DESC
                """,
                (ticket_id,),
            ).fetchall()
        return [self._comment_from_row(row) for row in rows]

    def get_history(self, ticket_id: int) -> list[TicketHistory]:
        with self.database.connect() as connection:
            self._ensure_exists(connection, ticket_id)
            rows = connection.execute(
                """
                SELECT * FROM ticket_history
                WHERE ticket_id = ? ORDER BY created_at DESC, id DESC
                """,
                (ticket_id,),
            ).fetchall()
        return [self._history_from_row(row) for row in rows]

    def count_all(self) -> int:
        with self.database.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS total FROM tickets").fetchone()
        return int(row["total"])

    def count_active(self) -> int:
        with self.database.connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total FROM tickets
                WHERE status IN ('Aberto', 'Em andamento', 'Aguardando')
                """
            ).fetchone()
        return int(row["total"])

    @staticmethod
    def _ensure_exists(connection: sqlite3.Connection, ticket_id: int) -> None:
        row = connection.execute(
            "SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
        if not row:
            raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")

    @staticmethod
    def _insert_history(
        connection: sqlite3.Connection,
        ticket_id: int,
        action: str,
        field_name: str,
        old_value: str,
        new_value: str,
        timestamp: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO ticket_history (
                ticket_id, action, field_name, old_value, new_value, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (ticket_id, action, field_name, old_value, new_value, timestamp),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Ticket:
        return Ticket(
            id=int(row["id"]),
            protocol=str(row["protocol"]),
            title=str(row["title"]),
            description=str(row["description"]),
            category=str(row["category"]),
            priority=str(row["priority"]),
            status=str(row["status"]),
            assignee=str(row["assignee"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    @staticmethod
    def _comment_from_row(row: sqlite3.Row) -> TicketComment:
        return TicketComment(
            id=int(row["id"]),
            ticket_id=int(row["ticket_id"]),
            author=str(row["author"]),
            content=str(row["content"]),
            created_at=str(row["created_at"]),
        )

    @staticmethod
    def _history_from_row(row: sqlite3.Row) -> TicketHistory:
        return TicketHistory(
            id=int(row["id"]),
            ticket_id=int(row["ticket_id"]),
            action=str(row["action"]),
            field_name=str(row["field_name"]),
            old_value=str(row["old_value"]),
            new_value=str(row["new_value"]),
            created_at=str(row["created_at"]),
        )
