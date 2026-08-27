import io
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from radar_desk.data.database import Database
from radar_desk.data.ticket_repository import TicketRepository
from radar_desk.main import run_self_test
from radar_desk.services.demo_data_service import DemoDataService
from radar_desk.services.update_service import UpdateCheckError, UpdateService


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


def opener_for(payload):
    def open_request(_request, timeout):
        assert timeout == 8.0
        return FakeResponse(json.dumps(payload).encode("utf-8"))

    return open_request


def test_update_service_detects_new_installer_and_ignores_current_version() -> None:
    payload = {
        "tag_name": "v1.1.0",
        "name": "Radar Desk 1.1",
        "html_url": "https://github.com/tulioradames/radar-desk/releases/tag/v1.1.0",
        "body": "Melhorias de estabilidade.",
        "published_at": "2026-09-01T12:00:00Z",
        "assets": [
            {
                "name": "RadarDesk-Setup-1.1.0.exe",
                "browser_download_url": "https://example.test/RadarDesk-Setup-1.1.0.exe",
            }
        ],
    }
    update = UpdateService("1.0.0", opener=opener_for(payload)).check()

    assert update is not None
    assert update.version == "1.1.0"
    assert update.installer_url.endswith(".exe")
    assert UpdateService("1.1.0", opener=opener_for(payload)).check() is None


def test_update_service_wraps_network_errors() -> None:
    def failing_opener(*_args, **_kwargs):
        raise OSError("offline")

    with pytest.raises(UpdateCheckError):
        UpdateService("1.0.0", opener=failing_opener).check()


def test_demo_data_is_complete_and_idempotent() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "demo.sqlite3")
        database.initialize()
        repository = TicketRepository(database)
        now = datetime(2026, 8, 17, 12, 0, tzinfo=timezone.utc)
        service = DemoDataService(database, repository, clock=lambda: now)

        assert service.load() == 6
        assert service.load() == 0
        assert service.is_loaded()
        tickets = repository.list_all()
        assert len(tickets) == 6
        assert {ticket.status for ticket in tickets} >= {
            "Aberto",
            "Em andamento",
            "Aguardando",
            "Resolvido",
            "Encerrado",
        }


def test_application_self_test_initializes_local_storage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("RADARDESK_DATA_DIR", str(tmp_path))

    assert run_self_test() == 0
    assert (tmp_path / "radar_desk.sqlite3").is_file()
    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / "arquivos").is_dir()
