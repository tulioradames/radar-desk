"""Configuração central e caminhos persistentes do aplicativo."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "Radar Desk"
APP_SLUG = "RadarDesk"
APP_VERSION = "0.2.0"
ORGANIZATION_NAME = "RadarDesk"


def _default_data_dir() -> Path:
    override = os.getenv("RADARDESK_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()

    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_SLUG
    return Path.home() / f".{APP_SLUG.lower()}"


@dataclass(frozen=True, slots=True)
class AppPaths:
    """Caminhos usados pelo aplicativo, agrupados para facilitar testes."""

    data_dir: Path

    @property
    def database(self) -> Path:
        return self.data_dir / "radar_desk.sqlite3"

    @property
    def logs_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def files_dir(self) -> Path:
        return self.data_dir / "arquivos"

    def ensure(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.files_dir.mkdir(parents=True, exist_ok=True)


def get_app_paths() -> AppPaths:
    return AppPaths(_default_data_dir())
