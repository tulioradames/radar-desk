from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from radar_desk.data.attachment_repository import AttachmentRepository
from radar_desk.data.database import Database
from radar_desk.data.ticket_repository import TicketRepository
from radar_desk.models.ticket import TicketInput
from radar_desk.services.attachment_service import (
    AttachmentService,
    AttachmentValidationError,
)
from radar_desk.services.ticket_service import TicketService


def build_services(root: Path) -> tuple[TicketService, AttachmentService]:
    database = Database(root / "test.sqlite3")
    database.initialize()
    tickets = TicketService(
        TicketRepository(database),
        clock=lambda: datetime(2026, 8, 11, 10, 0, tzinfo=timezone.utc),
    )
    attachments = AttachmentService(
        AttachmentRepository(database),
        root / "arquivos",
        clock=lambda: datetime(2026, 8, 11, 10, 5, tzinfo=timezone.utc),
    )
    return tickets, attachments


def test_files_are_copied_to_protocol_folders_and_recorded() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        tickets, attachments = build_services(root)
        ticket = tickets.create(
            TicketInput(
                title="Coletar evidências",
                description="Arquivos necessários para analisar o incidente.",
                category="Software",
                priority="Alta",
            )
        )
        sources = root / "fontes"
        sources.mkdir()
        source_files = [
            sources / "tela.png",
            sources / "relatorio.pdf",
            sources / "aplicacao.log",
        ]
        for index, source in enumerate(source_files, start=1):
            source.write_bytes(f"conteudo-{index}".encode())

        records = attachments.attach_many(ticket, source_files)

        assert [record.file_type for record in records] == ["image", "document", "log"]
        assert Path(records[0].file_path).parent.name == "imagens"
        assert Path(records[1].file_path).parent.name == "documentos"
        assert Path(records[2].file_path).parent.name == "diagnosticos"
        assert all(Path(record.file_path).exists() for record in records)
        assert len(attachments.list_for_ticket(ticket.id)) == 3
        assert sum(
            item.action == "Arquivo anexado" for item in tickets.get_history(ticket.id)
        ) == 3


def test_duplicate_file_names_are_preserved_with_unique_names() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        tickets, attachments = build_services(root)
        ticket = tickets.create(
            TicketInput(
                title="Arquivos duplicados",
                description="Duas capturas com o mesmo nome devem ser preservadas.",
                category="Software",
                priority="Baixa",
            )
        )
        source = root / "captura.png"
        source.write_bytes(b"imagem")

        first = attachments.attach(ticket, source)
        second = attachments.attach(ticket, source)

        assert first.stored_name == "captura.png"
        assert second.stored_name == "captura (2).png"
        assert Path(first.file_path).read_bytes() == b"imagem"
        assert Path(second.file_path).read_bytes() == b"imagem"


def test_unsupported_file_is_rejected_without_creating_record() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        tickets, attachments = build_services(root)
        ticket = tickets.create(
            TicketInput(
                title="Arquivo inválido",
                description="Um executável não deve ser anexado ao chamado.",
                category="Outros",
                priority="Média",
            )
        )
        source = root / "programa.exe"
        source.write_bytes(b"MZ")

        with pytest.raises(AttachmentValidationError, match="Formato não permitido"):
            attachments.attach(ticket, source)

        assert attachments.list_for_ticket(ticket.id) == []
