from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from radar_desk.data.auth_repository import AuthRepository
from radar_desk.data.database import Database
from radar_desk.services.auth_service import AuthError, AuthService


def test_first_admin_is_hashed_and_can_authenticate_offline() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        repository = AuthRepository(database)
        service = AuthService(
            repository,
            clock=lambda: datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc),
        )

        assert service.needs_setup()
        admin = service.setup_admin("admin.local", "Administrador Local", "Radar1234")

        assert admin.role == "Administrador"
        assert not service.needs_setup()
        row = repository.credentials_for("ADMIN.LOCAL")
        assert row["password_hash"] != "Radar1234"
        assert row["password_salt"]
        assert service.authenticate("admin.local", "Radar1234") == admin
        assert [entry.action for entry in service.list_audit()] == [
            "Login local",
            "Configuração inicial",
        ]


def test_roles_and_invalid_credentials_are_enforced() -> None:
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        service = AuthService(AuthRepository(database))
        admin = service.setup_admin("admin", "Admin", "Senha123")
        requester = service.create_user("solicitante", "Pessoa Solicitante", "Solicitante", "Senha456")
        attendant = service.create_user("atendente", "Pessoa Atendente", "Atendente", "Senha789")

        assert admin.can_administer
        assert attendant.can_manage_tickets
        assert not requester.can_manage_tickets
        with pytest.raises(AuthError, match="inválidos"):
            service.authenticate("admin", "senha-errada")
        with pytest.raises(AuthError, match="8 caracteres"):
            service.create_user("curto", "Senha Curta", "Solicitante", "abc")
