from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from radar_desk.data.auth_repository import AuthRepository
from radar_desk.data.database import Database
from radar_desk.data.sync_repository import SyncRepository
from radar_desk.data.ticket_repository import TicketRepository
from radar_desk.models.ticket import TicketInput
from radar_desk.services.auth_service import AuthService
from radar_desk.services.change_tracker import ChangeTracker
from radar_desk.services.ticket_service import TicketService, TicketValidationError


def test_requester_creates_offline_but_cannot_edit_or_delete() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        now = datetime(2026, 8, 13, 14, 0, tzinfo=timezone.utc)
        auth = AuthService(AuthRepository(database), clock=lambda: now)
        auth.setup_admin("admin", "Admin", "Radar123")
        user = auth.create_user("maria", "Maria Solicitante", "Solicitante", "Senha123")
        queue = SyncRepository(database)
        service = TicketService(
            TicketRepository(database), clock=lambda: now,
            tracker=ChangeTracker(user, auth, queue),
        )
        data = TicketInput(
            title="Sem acesso ao e-mail", description="A senha não permite o login.",
            category="Outros", priority="Alta",
        )

        ticket = service.create(data)

        assert ticket.category == "Acesso e permissões"
        assert queue.count_pending() == 1
        with pytest.raises(TicketValidationError, match="não permite"):
            service.update(ticket.id, data)
        with pytest.raises(TicketValidationError, match="administradores"):
            service.delete(ticket.id)
        assert any(entry.action == "Chamado criado" for entry in auth.list_audit())
