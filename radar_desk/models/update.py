"""Informações de uma versão publicada do Radar Desk."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    version: str
    name: str
    release_url: str
    installer_url: str
    notes: str
    published_at: str
