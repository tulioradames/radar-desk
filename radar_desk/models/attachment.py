"""Entidades dos arquivos e evidências vinculados a chamados."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TicketAttachment:
    id: int
    ticket_id: int
    original_name: str
    stored_name: str
    file_path: str
    file_type: str
    mime_type: str
    size_bytes: int
    created_at: str

    @property
    def type_label(self) -> str:
        return {
            "image": "Imagem",
            "document": "Documento",
            "log": "Log",
        }.get(self.file_type, "Arquivo")
