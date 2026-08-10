"""Persistência SQLite dos chamados."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from radar_desk.data.database import Database
from radar_desk.models.ticket import Ticket, TicketInput


class TicketNotFoundError(LookupError):
    pass


class TicketRepository:
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
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    protocol,
                    data.title,
                    data.description,
                    data.category,
                    data.priority,
                    data.status,
                    timestamp,
                    timestamp,
                ),
            )
            ticket_id = int(cursor.lastrowid)
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
            cursor = connection.execute(
                """
                UPDATE tickets
                SET title = ?, description = ?, category = ?, priority = ?,
                    status = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    data.title,
                    data.description,
                    data.category,
                    data.priority,
                    data.status,
                    timestamp,
                    ticket_id,
                ),
            )
            if cursor.rowcount == 0:
                raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")
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
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM tickets ORDER BY updated_at DESC, id DESC"
            ).fetchall()
        return [self._from_row(row) for row in rows]

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
    def _from_row(row: sqlite3.Row) -> Ticket:
        return Ticket(
            id=int(row["id"]),
            protocol=str(row["protocol"]),
            title=str(row["title"]),
            description=str(row["description"]),
            category=str(row["category"]),
            priority=str(row["priority"]),
            status=str(row["status"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
