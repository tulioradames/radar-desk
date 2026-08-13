"""Usuários locais, perfis e permissões."""

from __future__ import annotations

from dataclasses import dataclass


ROLES = ("Solicitante", "Atendente", "Administrador")


@dataclass(frozen=True, slots=True)
class User:
    id: int
    username: str
    display_name: str
    role: str
    active: bool
    created_at: str

    @property
    def can_manage_tickets(self) -> bool:
        return self.role in ("Atendente", "Administrador")

    @property
    def can_administer(self) -> bool:
        return self.role == "Administrador"


@dataclass(frozen=True, slots=True)
class AuditEntry:
    id: int
    user_id: int | None
    username: str
    action: str
    entity_type: str
    entity_id: str
    details: str
    created_at: str
