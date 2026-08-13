from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from radar_desk.data.database import Database
from radar_desk.data.ticket_repository import TicketNotFoundError, TicketRepository
from radar_desk.models.ticket import TicketFilter, TicketInput
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

        first = service.create(sample_input(assignee="Equipe N1"))
        second = service.create(sample_input(title="Impressora indisponível"))

        assert first.protocol == "RD-2026-0001"
        assert second.protocol == "RD-2026-0002"
        assert service.count_all() == 2
        assert service.count_active() == 2
        assert first.assignee == "Equipe N1"
        assert service.get_history(first.id)[0].action == "Chamado criado"

        current += timedelta(hours=1)
        updated = service.update(
            first.id,
            sample_input(
                title="Rede restabelecida",
                status="Resolvido",
                assignee="Técnico local",
            ),
        )
        assert updated.protocol == first.protocol
        assert updated.title == "Rede restabelecida"
        assert updated.status == "Resolvido"
        assert updated.updated_at != updated.created_at
        assert service.count_active() == 1
        assert updated.assignee == "Técnico local"

        closed = service.close_resolved(first.id)
        assert closed.status == "Encerrado"
        assert service.get_history(first.id)[0].action == "Chamado encerrado"

        comment = service.add_comment(
            first.id,
            "Conectividade confirmada com o solicitante.",
            "Túlio",
        )
        assert comment.author == "Túlio"
        assert len(service.get_comments(first.id)) == 1
        assert any(
            item.action == "Comentário adicionado"
            for item in service.get_history(first.id)
        )

        current += timedelta(minutes=30)
        reopened = service.reopen(first.id)
        assert reopened.status == "Aberto"
        assert service.get_history(first.id)[0].action == "Chamado reaberto"

        service.delete(second.id)
        third = service.create(sample_input(title="Novo problema de rede"))
        assert third.protocol == "RD-2026-0003"
        assert service.count_all() == 2


def test_general_search_and_operational_filters() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        current = datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc)
        service = TicketService(TicketRepository(database), clock=lambda: current)
        network = service.create(sample_input(assignee="Equipe Redes"))
        current += timedelta(days=2)
        service.create(
            sample_input(
                title="Instalar editor de texto",
                description="Instalação necessária para editar relatórios.",
                category="Software",
                priority="Baixa",
                status="Em andamento",
                assignee="Equipe Apps",
            )
        )

        assert service.search(TicketFilter(search=network.protocol)) == [network]
        assert service.search(TicketFilter(search="redes")) == [network]
        assert service.search(TicketFilter(category="Software"))[0].title.startswith(
            "Instalar"
        )
        assert len(service.search(TicketFilter(status="Em andamento"))) == 1
        assert len(service.search(TicketFilter(priority="Alta"))) == 1
        assert service.search(
            TicketFilter(start_date="2026-08-12", end_date="2026-08-12")
        )[0].category == "Software"

        with pytest.raises(TicketValidationError):
            service.search(
                TicketFilter(start_date="2026-08-15", end_date="2026-08-01")
            )
        with pytest.raises(TicketValidationError):
            service.reopen(network.id)


def test_ticket_validation_and_missing_records() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        service = TicketService(TicketRepository(database))

        with pytest.raises(TicketValidationError):
            service.create(sample_input(title="x"))
        with pytest.raises(TicketValidationError):
            service.create(sample_input(category="Categoria inexistente"))
        with pytest.raises(TicketValidationError):
            service.add_comment(999, "")
        with pytest.raises(TicketNotFoundError):
            service.get(999)
        with pytest.raises(TicketNotFoundError):
            service.delete(999)


def test_automatic_category_is_applied_when_category_is_others() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        service = TicketService(TicketRepository(database))

        ticket = service.create(
            sample_input(
                title="Impressora sem papel",
                description="Não consigo imprimir o relatório.",
                category="Outros",
            )
        )

        assert ticket.category == "Impressão"
