"""Coleta e anexo transparente de diagnóstico da estação Windows."""

from __future__ import annotations

import ctypes
import getpass
import json
import os
import platform
import re
import shutil
import socket
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from radar_desk.data.diagnostic_repository import DiagnosticRepository
from radar_desk.models.diagnostic import AttachedDiagnostic, DiagnosticSnapshot
from radar_desk.models.ticket import Ticket


@dataclass(frozen=True, slots=True)
class MemoryUsage:
    total: int
    used: int
    percent: float


@dataclass(frozen=True, slots=True)
class StorageUsage:
    drive: str
    total: int
    used: int
    free: int
    percent: float


class DiagnosticCollector:
    PING_TARGET = "1.1.1.1"

    def __init__(
        self,
        clock: Callable[[], datetime] | None = None,
        ip_provider: Callable[[], str] | None = None,
        memory_provider: Callable[[], MemoryUsage] | None = None,
        storage_provider: Callable[[], StorageUsage] | None = None,
        connection_probe: Callable[[], bool] | None = None,
        ping_probe: Callable[[], tuple[bool, float | None]] | None = None,
    ) -> None:
        self.clock = clock or (lambda: datetime.now().astimezone())
        self.ip_provider = ip_provider or self._local_ip
        self.memory_provider = memory_provider or self._memory_usage
        self.storage_provider = storage_provider or self._storage_usage
        self.connection_probe = connection_probe or self._connection_available
        self.ping_probe = ping_probe or self._ping

    def collect(self) -> DiagnosticSnapshot:
        memory = self.memory_provider()
        storage = self.storage_provider()
        ping_success, latency = self.ping_probe()
        connected = self.connection_probe() or ping_success
        return DiagnosticSnapshot(
            collected_at=self.clock().isoformat(timespec="seconds"),
            operating_system=platform.system() or "Não identificado",
            os_version=platform.platform() or platform.version() or "Não identificado",
            architecture=platform.machine() or "Não identificada",
            computer_name=socket.gethostname() or "Não identificado",
            user_name=getpass.getuser() or "Não identificado",
            local_ip=self.ip_provider(),
            memory_total_bytes=memory.total,
            memory_used_bytes=memory.used,
            memory_percent=memory.percent,
            storage_drive=storage.drive,
            storage_total_bytes=storage.total,
            storage_used_bytes=storage.used,
            storage_free_bytes=storage.free,
            storage_percent=storage.percent,
            connection_status="Conectado" if connected else "Sem conexão detectada",
            ping_target=self.PING_TARGET,
            ping_success=ping_success,
            ping_latency_ms=latency,
        )

    @staticmethod
    def _local_ip() -> str:
        connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            connection.connect(("8.8.8.8", 80))
            return str(connection.getsockname()[0])
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except OSError:
                return "Não identificado"
        finally:
            connection.close()

    @staticmethod
    def _memory_usage() -> MemoryUsage:
        if os.name == "nt":
            class MemoryStatus(ctypes.Structure):
                _fields_ = (
                    ("length", ctypes.c_ulong),
                    ("memory_load", ctypes.c_ulong),
                    ("total_physical", ctypes.c_ulonglong),
                    ("available_physical", ctypes.c_ulonglong),
                    ("total_page_file", ctypes.c_ulonglong),
                    ("available_page_file", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong),
                    ("available_virtual", ctypes.c_ulonglong),
                    ("available_extended_virtual", ctypes.c_ulonglong),
                )

            status = MemoryStatus()
            status.length = ctypes.sizeof(MemoryStatus)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                total = int(status.total_physical)
                used = total - int(status.available_physical)
                return MemoryUsage(total, used, float(status.memory_load))

        try:
            values: dict[str, int] = {}
            with open("/proc/meminfo", encoding="utf-8") as source:
                for line in source:
                    key, value = line.split(":", 1)
                    values[key] = int(value.strip().split()[0]) * 1024
            total = values.get("MemTotal", 0)
            available = values.get("MemAvailable", 0)
            used = max(0, total - available)
            percent = (used / total * 100) if total else 0.0
            return MemoryUsage(total, used, percent)
        except (OSError, ValueError):
            return MemoryUsage(0, 0, 0.0)

    @staticmethod
    def _storage_usage() -> StorageUsage:
        drive = os.getenv("SystemDrive")
        root = f"{drive}\\" if drive else (Path.home().anchor or str(Path.home()))
        usage = shutil.disk_usage(root)
        percent = (usage.used / usage.total * 100) if usage.total else 0.0
        return StorageUsage(root, usage.total, usage.used, usage.free, percent)

    @staticmethod
    def _connection_available() -> bool:
        try:
            connection = socket.create_connection(("1.1.1.1", 53), timeout=1.5)
            connection.close()
            return True
        except OSError:
            return False

    @classmethod
    def _ping(cls) -> tuple[bool, float | None]:
        command = (
            ["ping", "-n", "1", "-w", "1500", cls.PING_TARGET]
            if os.name == "nt"
            else ["ping", "-c", "1", "-W", "2", cls.PING_TARGET]
        )
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                errors="ignore",
                timeout=4,
                creationflags=flags,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False, None
        output = f"{result.stdout}\n{result.stderr}"
        match = re.search(r"(?:time|tempo)[=<]\s*(\d+(?:[.,]\d+)?)\s*ms", output, re.I)
        latency = float(match.group(1).replace(",", ".")) if match else None
        return result.returncode == 0, latency


class DiagnosticService:
    def __init__(
        self,
        repository: DiagnosticRepository,
        files_dir: Path,
        collector: DiagnosticCollector | None = None,
    ) -> None:
        self.repository = repository
        self.files_dir = files_dir
        self.collector = collector or DiagnosticCollector()

    def collect(self) -> DiagnosticSnapshot:
        return self.collector.collect()

    def attach(
        self,
        ticket: Ticket,
        snapshot: DiagnosticSnapshot,
        screenshot_png: bytes | None = None,
    ) -> AttachedDiagnostic:
        destination = self.files_dir / ticket.protocol / "diagnosticos"
        destination.mkdir(parents=True, exist_ok=True)
        collected = datetime.fromisoformat(snapshot.collected_at)
        stem = collected.strftime("diagnostico_%Y%m%d_%H%M%S_%f")
        screenshot_path = destination / f"{stem}.png" if screenshot_png else None
        if screenshot_path and screenshot_png:
            screenshot_path.write_bytes(screenshot_png)

        report_path = destination / f"{stem}.json"
        payload = {
            "ticket_id": ticket.id,
            "protocol": ticket.protocol,
            "diagnostic": snapshot.to_dict(),
            "screenshot_included": bool(screenshot_path),
            "screenshot_path": str(screenshot_path) if screenshot_path else "",
        }
        report_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.repository.create(
            ticket.id,
            snapshot,
            str(report_path),
            str(screenshot_path) if screenshot_path else "",
        )

    def list_for_ticket(self, ticket_id: int) -> list[AttachedDiagnostic]:
        return self.repository.list_for_ticket(ticket_id)
