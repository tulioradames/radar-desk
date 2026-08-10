"""Entidades do diagnóstico transparente da estação de trabalho."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def format_bytes(value: int) -> str:
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} B"
        amount /= 1024
    return f"{amount:.1f} TB"


@dataclass(frozen=True, slots=True)
class DiagnosticSnapshot:
    collected_at: str
    operating_system: str
    os_version: str
    architecture: str
    computer_name: str
    user_name: str
    local_ip: str
    memory_total_bytes: int
    memory_used_bytes: int
    memory_percent: float
    storage_drive: str
    storage_total_bytes: int
    storage_used_bytes: int
    storage_free_bytes: int
    storage_percent: float
    connection_status: str
    ping_target: str
    ping_success: bool
    ping_latency_ms: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def display_items(self) -> tuple[tuple[str, str], ...]:
        latency = (
            f"{self.ping_latency_ms:.1f} ms"
            if self.ping_latency_ms is not None
            else "Sem resposta"
        )
        return (
            ("Coletado em", self.collected_at),
            ("Sistema operacional", self.operating_system),
            ("Versão do sistema", self.os_version),
            ("Arquitetura", self.architecture),
            ("Nome do computador", self.computer_name),
            ("Usuário local", self.user_name),
            ("IP local", self.local_ip),
            ("Memória total", format_bytes(self.memory_total_bytes)),
            ("Memória em uso", format_bytes(self.memory_used_bytes)),
            ("Uso de memória", f"{self.memory_percent:.1f}%"),
            ("Unidade analisada", self.storage_drive),
            ("Armazenamento total", format_bytes(self.storage_total_bytes)),
            ("Armazenamento usado", format_bytes(self.storage_used_bytes)),
            ("Armazenamento livre", format_bytes(self.storage_free_bytes)),
            ("Uso de armazenamento", f"{self.storage_percent:.1f}%"),
            ("Estado da conexão", self.connection_status),
            ("Destino do ping", self.ping_target),
            ("Resultado do ping", "Sucesso" if self.ping_success else "Falha"),
            ("Latência do ping", latency),
        )


@dataclass(frozen=True, slots=True)
class AttachedDiagnostic:
    id: int
    ticket_id: int
    data: dict[str, Any]
    report_path: str
    screenshot_path: str
    created_at: str
