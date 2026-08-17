"""Verificação segura de novas versões publicadas no GitHub."""

from __future__ import annotations

import json
import re
import urllib.request
from collections.abc import Callable
from typing import Any

from radar_desk.models.update import UpdateInfo


class UpdateCheckError(RuntimeError):
    pass


class UpdateService:
    API_URL = "https://api.github.com/repos/tulioradames/radar-desk/releases/latest"

    def __init__(
        self,
        current_version: str,
        opener: Callable[..., Any] | None = None,
        timeout: float = 8.0,
    ) -> None:
        self.current_version = current_version
        self.opener = opener or urllib.request.urlopen
        self.timeout = timeout

    def check(self) -> UpdateInfo | None:
        request = urllib.request.Request(
            self.API_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"RadarDesk/{self.current_version}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with self.opener(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as error:
            raise UpdateCheckError(
                "Não foi possível consultar as atualizações agora."
            ) from error

        version = str(payload.get("tag_name") or "").strip().lstrip("vV")
        if not version:
            raise UpdateCheckError("A versão publicada não possui uma identificação válida.")
        if self._version_tuple(version) <= self._version_tuple(self.current_version):
            return None

        assets = payload.get("assets") or []
        installer_url = ""
        for asset in assets:
            name = str(asset.get("name") or "").lower()
            if name.endswith(".exe") and ("setup" in name or "radardesk" in name):
                installer_url = str(asset.get("browser_download_url") or "")
                break
        return UpdateInfo(
            version=version,
            name=str(payload.get("name") or f"Radar Desk v{version}"),
            release_url=str(payload.get("html_url") or ""),
            installer_url=installer_url,
            notes=str(payload.get("body") or ""),
            published_at=str(payload.get("published_at") or ""),
        )

    @staticmethod
    def _version_tuple(value: str) -> tuple[int, int, int]:
        numbers = [int(part) for part in re.findall(r"\d+", value)[:3]]
        numbers.extend([0] * (3 - len(numbers)))
        return tuple(numbers)  # type: ignore[return-value]
