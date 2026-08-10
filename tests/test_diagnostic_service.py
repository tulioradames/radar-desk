import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from radar_desk.data.database import Database
from radar_desk.data.diagnostic_repository import DiagnosticRepository
from radar_desk.data.ticket_repository import TicketRepository
from radar_desk.models.ticket import TicketInput
from radar_desk.services.diagnostic_service import (
    DiagnosticCollector,
    DiagnosticService,
    MemoryUsage,
    StorageUsage,
)
from radar_desk.services.ticket_service import TicketService


def deterministic_collector() -> DiagnosticCollector:
    return DiagnosticCollector(
        clock=lambda: datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc),
        ip_provider=lambda: "192.168.1.25",
        memory_provider=lambda: MemoryUsage(
            total=16 * 1024**3,
            used=8 * 1024**3,
            percent=50.0,
        ),
        storage_provider=lambda: StorageUsage(
            drive="C:\\",
            total=500 * 1024**3,
            used=200 * 1024**3,
            free=300 * 1024**3,
            percent=40.0,
        ),
        connection_probe=lambda: True,
        ping_probe=lambda: (True, 12.5),
    )


def test_collector_exposes_every_previewed_field() -> None:
    snapshot = deterministic_collector().collect()

    assert snapshot.local_ip == "192.168.1.25"
    assert snapshot.memory_percent == 50.0
    assert snapshot.storage_free_bytes == 300 * 1024**3
    assert snapshot.connection_status == "Conectado"
    assert snapshot.ping_success is True
    assert snapshot.ping_latency_ms == 12.5
    assert len(snapshot.display_items()) == 19


def test_diagnostic_is_written_and_attached_to_ticket() -> None:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        database = Database(root / "test.sqlite3")
        database.initialize()
        ticket_service = TicketService(TicketRepository(database))
        ticket = ticket_service.create(
            TicketInput(
                title="Falha de desempenho",
                description="O computador apresenta lentidão durante o uso.",
                category="Hardware",
                priority="Alta",
            )
        )
        service = DiagnosticService(
            DiagnosticRepository(database),
            root / "arquivos",
            deterministic_collector(),
        )
        snapshot = service.collect()

        attached = service.attach(ticket, snapshot, b"fake-png-content")

        report_path = Path(attached.report_path)
        screenshot_path = Path(attached.screenshot_path)
        assert report_path.exists()
        assert screenshot_path.exists()
        assert screenshot_path.parent.name == "diagnosticos"
        assert screenshot_path.parent.parent.name == ticket.protocol
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        assert payload["protocol"] == ticket.protocol
        assert payload["diagnostic"]["local_ip"] == "192.168.1.25"
        assert payload["screenshot_included"] is True
        assert service.list_for_ticket(ticket.id)[0].id == attached.id
        assert any(
            item.action == "Diagnóstico anexado"
            for item in ticket_service.get_history(ticket.id)
        )
