"""Entidades da fila de sincronização local."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SyncEvent:
    id: int
    entity_type: str
    entity_id: str
    operation: str
    payload: dict[str, Any]
    local_version: int
    status: str
    attempts: int
    last_error: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class SyncResult:
    processed: int
    succeeded: int
    failed: int
    conflicts: int
