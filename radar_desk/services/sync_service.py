"""Sincronização opcional com Supabase preservando a operação offline."""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime
from typing import Any

from radar_desk.data.auth_repository import AuthRepository
from radar_desk.data.database import Database
from radar_desk.data.sync_repository import SyncRepository
from radar_desk.models.sync import SyncEvent, SyncResult
from radar_desk.models.user import User


class SyncConfigurationError(RuntimeError):
    pass


class SupabaseClient:
    TABLE = "radar_desk_changes"

    def __init__(
        self, url: str = "", anon_key: str = "", access_token: str = "",
        timeout: float = 8.0,
    ) -> None:
        self.url = url.rstrip("/")
        self.anon_key = anon_key
        self.access_token = access_token
        self.timeout = timeout

    @classmethod
    def from_environment(cls) -> "SupabaseClient":
        return cls(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_ANON_KEY", ""),
            os.getenv("SUPABASE_ACCESS_TOKEN", ""),
        )

    @property
    def configured(self) -> bool:
        return bool(self.url and self.anon_key and self.access_token)

    def fetch(self, entity_type: str, entity_id: str) -> dict[str, Any] | None:
        self._ensure_configured()
        query = urllib.parse.urlencode(
            {"entity_type": f"eq.{entity_type}", "entity_id": f"eq.{entity_id}", "limit": "1"}
        )
        response = self._request("GET", f"{self._endpoint()}?{query}")
        records = json.loads(response.decode("utf-8"))
        return records[0] if records else None

    def upsert(self, event: SyncEvent, payload: dict[str, Any]) -> None:
        self._ensure_configured()
        record = {
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "operation": event.operation,
            "payload": payload,
            "local_version": event.local_version,
            "updated_at": event.updated_at,
        }
        endpoint = f"{self._endpoint()}?on_conflict=entity_type,entity_id"
        self._request(
            "POST", endpoint, json.dumps(record, ensure_ascii=False).encode("utf-8"),
            {"Prefer": "resolution=merge-duplicates,return=minimal"},
        )

    def _request(
        self, method: str, url: str, data: bytes | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> bytes:
        headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        headers.update(extra_headers or {})
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase respondeu HTTP {error.code}: {detail[:300]}") from error

    def _endpoint(self) -> str:
        return f"{self.url}/rest/v1/{self.TABLE}"

    def _ensure_configured(self) -> None:
        if not self.configured:
            raise SyncConfigurationError(
                "Configure SUPABASE_URL, SUPABASE_ANON_KEY e SUPABASE_ACCESS_TOKEN para sincronizar."
            )


class SyncService:
    def __init__(
        self,
        database: Database,
        repository: SyncRepository,
        audit_repository: AuthRepository,
        user: User,
        client: SupabaseClient | None = None,
        clock: Callable[[], datetime] | None = None,
        connection_probe: Callable[[], bool] | None = None,
    ) -> None:
        self.database = database
        self.repository = repository
        self.audit_repository = audit_repository
        self.user = user
        self.client = client or SupabaseClient.from_environment()
        self.clock = clock or (lambda: datetime.now().astimezone())
        self.connection_probe = connection_probe or self._connection_available

    @property
    def configured(self) -> bool:
        return self.client.configured

    def pending_count(self) -> int:
        return self.repository.count_pending()

    def synchronize(self) -> SyncResult:
        events = self.repository.pending()
        if not events:
            return SyncResult(0, 0, 0, 0)
        if not self.configured:
            raise SyncConfigurationError("Supabase ainda não configurado. A fila local foi preservada.")
        if not self.connection_probe():
            raise ConnectionError("Sem conexão. A fila local será sincronizada quando a internet retornar.")
        succeeded = failed = conflicts = 0
        for event in events:
            try:
                remote = self.client.fetch(event.entity_type, event.entity_id)
                payload = event.payload
                if remote:
                    winner = self.resolve_conflict(event, remote)
                    if winner == "remote":
                        payload = dict(remote.get("payload") or {})
                        self._apply_remote(
                            event.entity_type, str(remote.get("operation") or event.operation), payload
                        )
                        conflicts += 1
                        self.repository.mark_done(event.id, self.clock())
                        succeeded += 1
                        continue
                    if winner == "local":
                        conflicts += 1
                self.client.upsert(event, payload)
                self.repository.mark_done(event.id, self.clock())
                succeeded += 1
            except Exception as error:
                self.repository.mark_failed(event.id, str(error), self.clock())
                failed += 1
        self.audit_repository.add_audit(
            self.user, "Sincronização executada", "sync", "",
            f"sucesso={succeeded}; falhas={failed}; conflitos={conflicts}", self.clock()
        )
        return SyncResult(len(events), succeeded, failed, conflicts)

    @staticmethod
    def resolve_conflict(event: SyncEvent, remote: dict[str, Any]) -> str:
        remote_version = int(remote.get("local_version") or 0)
        if event.local_version != remote_version:
            return "local" if event.local_version > remote_version else "remote"
        local_time = str(event.payload.get("updated_at") or event.updated_at)
        remote_payload = remote.get("payload") or {}
        remote_time = str(remote_payload.get("updated_at") or remote.get("updated_at") or "")
        return "local" if local_time >= remote_time else "remote"

    def _apply_remote(self, entity_type: str, operation: str, payload: dict[str, Any]) -> None:
        if entity_type == "ticket_rating":
            with self.database.connect() as connection:
                ticket = connection.execute(
                    "SELECT id FROM tickets WHERE protocol = ?", (payload.get("protocol"),)
                ).fetchone()
                if not ticket:
                    return
                connection.execute(
                    """
                    INSERT INTO ticket_ratings (
                        ticket_id, rating, comment, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(ticket_id) DO UPDATE SET
                        rating=excluded.rating,
                        comment=excluded.comment,
                        updated_at=excluded.updated_at
                    """,
                    (
                        int(ticket["id"]),
                        int(payload.get("rating") or 0),
                        str(payload.get("comment") or ""),
                        str(payload.get("created_at") or payload.get("changed_at") or self.clock().isoformat(timespec="seconds")),
                        str(payload.get("updated_at") or payload.get("changed_at") or self.clock().isoformat(timespec="seconds")),
                    ),
                )
            return
        if entity_type != "ticket" or not payload.get("protocol"):
            return
        with self.database.connect() as connection:
            if operation == "delete":
                connection.execute("DELETE FROM tickets WHERE protocol = ?", (payload["protocol"],))
                return
            connection.execute(
                """
                INSERT INTO tickets (
                    protocol, title, description, category, priority, status,
                    assignee, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(protocol) DO UPDATE SET
                    title=excluded.title, description=excluded.description,
                    category=excluded.category, priority=excluded.priority,
                    status=excluded.status, assignee=excluded.assignee,
                    updated_at=excluded.updated_at
                """,
                tuple(payload.get(key, "") for key in (
                    "protocol", "title", "description", "category", "priority",
                    "status", "assignee", "created_at", "updated_at"
                )),
            )

    @staticmethod
    def _connection_available() -> bool:
        try:
            connection = socket.create_connection(("1.1.1.1", 53), timeout=1.5)
            connection.close()
            return True
        except OSError:
            return False
