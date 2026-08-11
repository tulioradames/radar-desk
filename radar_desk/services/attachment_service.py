"""Regras para armazenamento local de arquivos e evidências."""

from __future__ import annotations

import mimetypes
import re
import shutil
from collections.abc import Callable, Iterable
from datetime import datetime
from pathlib import Path

from radar_desk.data.attachment_repository import AttachmentRepository
from radar_desk.models.attachment import TicketAttachment
from radar_desk.models.ticket import Ticket


class AttachmentValidationError(ValueError):
    pass


class AttachmentService:
    IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
    DOCUMENT_EXTENSIONS = {
        ".csv",
        ".doc",
        ".docx",
        ".odt",
        ".pdf",
        ".ppt",
        ".pptx",
        ".rtf",
        ".xls",
        ".xlsx",
        ".zip",
    }
    LOG_EXTENSIONS = {".ini", ".json", ".log", ".txt", ".xml", ".yaml", ".yml"}
    MAX_FILE_SIZE = 50 * 1024 * 1024

    def __init__(
        self,
        repository: AttachmentRepository,
        files_dir: Path,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.files_dir = Path(files_dir)
        self.clock = clock or (lambda: datetime.now().astimezone())

    def attach_many(
        self, ticket: Ticket, source_paths: Iterable[Path | str]
    ) -> list[TicketAttachment]:
        paths = list(source_paths)
        if not paths:
            raise AttachmentValidationError("Selecione pelo menos um arquivo.")
        return [self.attach(ticket, source) for source in paths]

    def attach(self, ticket: Ticket, source_path: Path | str) -> TicketAttachment:
        source = Path(source_path).expanduser().resolve()
        if not source.is_file():
            raise AttachmentValidationError(f"Arquivo não encontrado: {source}")
        size = source.stat().st_size
        if size > self.MAX_FILE_SIZE:
            raise AttachmentValidationError(
                f"{source.name} excede o limite de 50 MB por arquivo."
            )
        file_type = self.classify(source)
        folders = self.ensure_ticket_folders(ticket.protocol)
        destination = self._unique_destination(
            folders[self._folder_key(file_type)], self._safe_name(source.name)
        )
        try:
            shutil.copy2(source, destination)
            mime_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
            return self.repository.create(
                ticket.id,
                source.name,
                destination.name,
                str(destination),
                file_type,
                mime_type,
                size,
                self.clock(),
            )
        except Exception:
            destination.unlink(missing_ok=True)
            raise

    def list_for_ticket(self, ticket_id: int) -> list[TicketAttachment]:
        return self.repository.list_for_ticket(ticket_id)

    def ensure_ticket_folders(self, protocol: str) -> dict[str, Path]:
        root = self.files_dir / protocol
        folders = {
            "image": root / "imagens",
            "document": root / "documentos",
            "diagnostic": root / "diagnosticos",
        }
        for folder in folders.values():
            folder.mkdir(parents=True, exist_ok=True)
        return folders

    @classmethod
    def classify(cls, path: Path) -> str:
        extension = path.suffix.lower()
        if extension in cls.IMAGE_EXTENSIONS:
            return "image"
        if extension in cls.DOCUMENT_EXTENSIONS:
            return "document"
        if extension in cls.LOG_EXTENSIONS:
            return "log"
        supported = sorted(
            cls.IMAGE_EXTENSIONS | cls.DOCUMENT_EXTENSIONS | cls.LOG_EXTENSIONS
        )
        raise AttachmentValidationError(
            f"Formato não permitido: {extension or 'sem extensão'}. "
            f"Use um destes formatos: {', '.join(supported)}"
        )

    @staticmethod
    def _folder_key(file_type: str) -> str:
        return "diagnostic" if file_type == "log" else file_type

    @staticmethod
    def _safe_name(name: str) -> str:
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
        return sanitized or "arquivo"

    @staticmethod
    def _unique_destination(folder: Path, file_name: str) -> Path:
        candidate = folder / file_name
        if not candidate.exists():
            return candidate
        stem = Path(file_name).stem
        suffix = Path(file_name).suffix
        counter = 2
        while True:
            candidate = folder / f"{stem} ({counter}){suffix}"
            if not candidate.exists():
                return candidate
            counter += 1
