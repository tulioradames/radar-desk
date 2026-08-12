"""Persistência dos arquivos anexados aos chamados."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from radar_desk.data.database import Database
from radar_desk.data.ticket_repository import TicketNotFoundError
from radar_desk.models.attachment import TicketAttachment


class AttachmentRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        ticket_id: int,
        original_name: str,
        stored_name: str,
        file_path: str,
        file_type: str,
        mime_type: str,
        size_bytes: int,
        now: datetime,
    ) -> TicketAttachment:
        timestamp = now.isoformat(timespec="seconds")
        with self.database.connect() as connection:
            if not connection.execute(
                "SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone():
                raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")
            cursor = connection.execute(
                """
                INSERT INTO ticket_attachments (
                    ticket_id, original_name, stored_name, file_path, file_type,
                    mime_type, size_bytes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_id,
                    original_name,
                    stored_name,
                    file_path,
                    file_type,
                    mime_type,
                    size_bytes,
                    timestamp,
                ),
            )
            attachment_id = int(cursor.lastrowid)
            connection.execute(
                "UPDATE tickets SET updated_at = ? WHERE id = ?",
                (timestamp, ticket_id),
            )
            connection.execute(
                """
                INSERT INTO ticket_history (
                    ticket_id, action, field_name, old_value, new_value, created_at
                ) VALUES (?, 'Arquivo anexado', 'attachment', '', ?, ?)
                """,
                (ticket_id, original_name, timestamp),
            )
            row = connection.execute(
                "SELECT * FROM ticket_attachments WHERE id = ?", (attachment_id,)
            ).fetchone()
        return self._from_row(row)

    def list_for_ticket(self, ticket_id: int) -> list[TicketAttachment]:
        with self.database.connect() as connection:
            if not connection.execute(
                "SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone():
                raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")
            rows = connection.execute(
                """
                SELECT * FROM ticket_attachments
                WHERE ticket_id = ? ORDER BY created_at DESC, id DESC
                """,
                (ticket_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> TicketAttachment:
        return TicketAttachment(
            id=int(row["id"]),
            ticket_id=int(row["ticket_id"]),
            original_name=str(row["original_name"]),
            stored_name=str(row["stored_name"]),
            file_path=str(row["file_path"]),
            file_type=str(row["file_type"]),
            mime_type=str(row["mime_type"]),
            size_bytes=int(row["size_bytes"]),
            created_at=str(row["created_at"]),
        )
