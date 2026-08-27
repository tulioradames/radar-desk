from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from radar_desk.data.auth_repository import AuthRepository
from radar_desk.data.database import Database
from radar_desk.data.sync_repository import SyncRepository
from radar_desk.models.sync import SyncEvent
from radar_desk.services.auth_service import AuthService
from radar_desk.services.sync_service import SyncService


NOW = datetime(2026, 8, 13, 12, 0, tzinfo=timezone.utc)


class FakeSupabase:
    configured = True

    def __init__(self, remote=None) -> None:
        self.remote = remote
        self.upserts = []

    def fetch(self, entity_type: str, entity_id: str):
        return self.remote

    def upsert(self, event, payload) -> None:
        self.upserts.append((event, payload))


def test_queue_compacts_repeated_changes_without_duplicates() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        repository = SyncRepository(database)

        first = repository.enqueue("ticket", "RD-2026-0001", "create", {"title": "A"}, NOW)
        second = repository.enqueue("ticket", "RD-2026-0001", "update", {"title": "B"}, NOW)

        assert first.id == second.id
        assert second.local_version == 2
        assert second.operation == "update"
        assert repository.count_pending() == 1


def test_sync_marks_events_done_and_audits_result() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        auth_repository = AuthRepository(database)
        auth = AuthService(auth_repository, clock=lambda: NOW)
        user = auth.setup_admin("admin", "Admin Local", "Radar123")
        repository = SyncRepository(database)
        repository.enqueue(
            "ticket", "RD-2026-0001", "update",
            {"protocol": "RD-2026-0001", "updated_at": NOW.isoformat()}, NOW,
        )
        client = FakeSupabase()
        service = SyncService(
            database, repository, auth_repository, user, client=client,
            clock=lambda: NOW, connection_probe=lambda: True,
        )

        result = service.synchronize()

        assert result.succeeded == 1
        assert result.failed == 0
        assert repository.count_pending() == 0
        assert len(client.upserts) == 1
        assert auth.list_audit()[0].action == "Sincronização executada"


def test_conflict_resolution_prefers_newest_version_then_timestamp() -> None:
    event = SyncEvent(
        id=1, entity_type="ticket", entity_id="RD-2026-0001", operation="update",
        payload={"updated_at": NOW.isoformat()}, local_version=2, status="pending",
        attempts=0, last_error="", created_at=NOW.isoformat(), updated_at=NOW.isoformat(),
    )

    assert SyncService.resolve_conflict(event, {"local_version": 1}) == "local"
    assert SyncService.resolve_conflict(
        event,
        {
            "local_version": 2,
            "payload": {"updated_at": (NOW + timedelta(minutes=1)).isoformat()},
        },
    ) == "remote"
