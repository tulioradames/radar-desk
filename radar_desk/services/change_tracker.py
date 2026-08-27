"""Registra auditoria e alterações pendentes sem exigir internet."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any

from radar_desk.data.sync_repository import SyncRepository
from radar_desk.models.user import User
from radar_desk.services.auth_service import AuthService


class ChangeTracker:
    def __init__(
        self,
        user: User,
        auth_service: AuthService,
        sync_repository: SyncRepository,
    ) -> None:
        self.user = user
        self.auth_service = auth_service
        self.sync_repository = sync_repository

    def record(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        operation: str,
        payload: Any,
    ) -> None:
        serialized = asdict(payload) if is_dataclass(payload) else dict(payload)
        now = self.auth_service.clock()
        serialized["changed_by"] = self.user.username
        serialized["changed_at"] = now.isoformat(timespec="seconds")
        self.sync_repository.enqueue(entity_type, entity_id, operation, serialized, now)
        self.auth_service.audit(
            self.user, action, entity_type, entity_id, operation
        )
