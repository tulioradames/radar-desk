"""Consultas SQLite e persistência das avaliações de atendimento."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from radar_desk.data.database import Database
from radar_desk.data.ticket_repository import TicketNotFoundError, TicketRepository
from radar_desk.models.report import ReportFilter, TicketRating
from radar_desk.models.ticket import Ticket, TicketFilter


class ReportRepository:
    def __init__(
        self,
        database: Database,
        ticket_repository: TicketRepository | None = None,
    ) -> None:
        self.database = database
        self.ticket_repository = ticket_repository or TicketRepository(database)

    def list_tickets(self, filters: ReportFilter) -> list[Ticket]:
        return self.ticket_repository.list_filtered(
            TicketFilter(start_date=filters.start_date, end_date=filters.end_date)
        )

    def resolution_datetimes(self, ticket_ids: list[int]) -> dict[int, str]:
        if not ticket_ids:
            return {}
        placeholders = ", ".join("?" for _ in ticket_ids)
        with self.database.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    t.id,
                    COALESCE(
                        MIN(
                            CASE
                                WHEN h.field_name = 'status'
                                 AND h.new_value IN ('Resolvido', 'Encerrado')
                                THEN h.created_at
                            END
                        ),
                        CASE
                            WHEN t.status IN ('Resolvido', 'Encerrado')
                            THEN t.updated_at
                        END
                    ) AS resolved_at
                FROM tickets AS t
                LEFT JOIN ticket_history AS h ON h.ticket_id = t.id
                WHERE t.id IN ({placeholders})
                GROUP BY t.id
                """,
                ticket_ids,
            ).fetchall()
        return {
            int(row["id"]): str(row["resolved_at"])
            for row in rows
            if row["resolved_at"]
        }

    def rating_summary(self, ticket_ids: list[int]) -> tuple[float | None, int]:
        if not ticket_ids:
            return None, 0
        placeholders = ", ".join("?" for _ in ticket_ids)
        with self.database.connect() as connection:
            row = connection.execute(
                f"""
                SELECT AVG(rating) AS average_rating, COUNT(*) AS total
                FROM ticket_ratings
                WHERE ticket_id IN ({placeholders})
                """,
                ticket_ids,
            ).fetchone()
        total = int(row["total"]) if row else 0
        average = float(row["average_rating"]) if row and row["average_rating"] else None
        return average, total

    def save_rating(
        self,
        ticket_id: int,
        rating: int,
        comment: str,
        now: datetime,
    ) -> TicketRating:
        timestamp = now.isoformat(timespec="seconds")
        with self.database.connect() as connection:
            ticket = connection.execute(
                "SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()
            if not ticket:
                raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")
            connection.execute(
                """
                INSERT INTO ticket_ratings (
                    ticket_id, rating, comment, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(ticket_id) DO UPDATE SET
                    rating = excluded.rating,
                    comment = excluded.comment,
                    updated_at = excluded.updated_at
                """,
                (ticket_id, rating, comment, timestamp, timestamp),
            )
            row = connection.execute(
                "SELECT * FROM ticket_ratings WHERE ticket_id = ?", (ticket_id,)
            ).fetchone()
        return self._rating_from_row(row)

    def get_rating(self, ticket_id: int) -> TicketRating | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM ticket_ratings WHERE ticket_id = ?", (ticket_id,)
            ).fetchone()
        return self._rating_from_row(row) if row else None

    @staticmethod
    def _rating_from_row(row: sqlite3.Row) -> TicketRating:
        return TicketRating(
            id=int(row["id"]),
            ticket_id=int(row["ticket_id"]),
            rating=int(row["rating"]),
            comment=str(row["comment"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
