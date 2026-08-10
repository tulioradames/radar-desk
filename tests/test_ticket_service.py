from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from radar_desk.data.database import Database
from radar_desk.data.ticket_repository import TicketNotFoundError, TicketRepository
from radar_desk.models.ticket import TicketInput
from radar_desk.services.ticket_service import TicketService, TicketValidationError


def sample_input(**changes: str) -> TicketInput:
    values = {
        "title": "Falha de acesso à rede",
        "description": "O computador não consegue acessar a rede interna.",
        "category": "Rede e internet",
        "priority": "Alta",
        "status": "Aberto",
    }
    values.update(changes)
    return TicketInput(**values)


def test_full_ticket_crud_and_protocol_sequence() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        current = datetime(2026, 8, 10, 14, 30, tzinfo=timezone.utc)
        service = TicketService(TicketRepository(database), clock=lambda: current)

        first = service.create(sample_input())
        second = service.create(sample_input(title="Impressora indisponível"))

        assert first.protocol == "RD-2026-0001"
        assert second.protocol == "RD-2026-0002"
        assert service.count_all() == 2
        assert service.count_active() == 2

        current += timedelta(hours=1)
        updated = service.update(
            first.id,
            sample_input(title="Rede restabelecida", status="Resolvido"),
        )
        assert updated.protocol == first.protocol
        assert updated.title == "Rede restabelecida"
        assert updated.status == "Resolvido"
        assert updated.updated_at != updated.created_at
        assert service.count_active() == 1

        service.delete(second.id)
        third = service.create(sample_input(title="Novo problema de rede"))
        assert third.protocol == "RD-2026-0003"
        assert service.count_all() == 2


def test_ticket_validation_and_missing_records() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        service = TicketService(TicketRepository(database))

        with pytest.raises(TicketValidationError):
            service.create(sample_input(title="x"))
        with pytest.raises(TicketValidationError):
            service.create(sample_input(category="Categoria inexistente"))
        with pytest.raises(TicketNotFoundError):
            service.get(999)
        with pytest.raises(TicketNotFoundError):
            service.delete(999)
