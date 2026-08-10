"""Persistência dos relatórios de diagnóstico vinculados a chamados."""

from __future__ import annotations

import json
import sqlite3

from radar_desk.data.database import Database
from radar_desk.data.ticket_repository import TicketNotFoundError
from radar_desk.models.diagnostic import AttachedDiagnostic, DiagnosticSnapshot


class DiagnosticRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        ticket_id: int,
        snapshot: DiagnosticSnapshot,
        report_path: str,
        screenshot_path: str,
    ) -> AttachedDiagnostic:
        data_json = json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2)
        with self.database.connect() as connection:
            if not connection.execute(
                "SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone():
                raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")
            cursor = connection.execute(
                """
                INSERT INTO ticket_diagnostics (
                    ticket_id, data_json, report_path, screenshot_path, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    ticket_id,
                    data_json,
                    report_path,
                    screenshot_path,
                    snapshot.collected_at,
                ),
            )
            row = connection.execute(
                "SELECT * FROM ticket_diagnostics WHERE id = ?",
                (int(cursor.lastrowid),),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO ticket_history (
                    ticket_id, action, field_name, old_value, new_value, created_at
                ) VALUES (?, 'Diagnóstico anexado', 'diagnostic', '', ?, ?)
                """,
                (ticket_id, report_path, snapshot.collected_at),
            )
        return self._from_row(row)

    def list_for_ticket(self, ticket_id: int) -> list[AttachedDiagnostic]:
        with self.database.connect() as connection:
            if not connection.execute(
                "SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone():
                raise TicketNotFoundError(f"Chamado {ticket_id} não encontrado")
            rows = connection.execute(
                """
                SELECT * FROM ticket_diagnostics
                WHERE ticket_id = ? ORDER BY created_at DESC, id DESC
                """,
                (ticket_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AttachedDiagnostic:
        return AttachedDiagnostic(
            id=int(row["id"]),
            ticket_id=int(row["ticket_id"]),
            data=json.loads(str(row["data_json"])),
            report_path=str(row["report_path"]),
            screenshot_path=str(row["screenshot_path"]),
            created_at=str(row["created_at"]),
        )
