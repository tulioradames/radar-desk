"""Tela de arquivos, evidências e visualização de imagens."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QDragEnterEvent, QDropEvent, QPixmap, QTransform
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from radar_desk.models.attachment import TicketAttachment
from radar_desk.models.diagnostic import format_bytes
from radar_desk.models.ticket import Ticket
from radar_desk.services.attachment_service import (
    AttachmentService,
    AttachmentValidationError,
)
from radar_desk.services.ticket_service import TicketService


class FileDropZone(QFrame):
    files_dropped = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(92)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(3)
        icon = QLabel("⇩")
        icon.setObjectName("dropIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Arraste arquivos para cá")
        title.setObjectName("dropTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail = QLabel("Imagens, documentos e logs · até 50 MB por arquivo")
        detail.setProperty("muted", True)
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(detail)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls() and any(
            url.isLocalFile() for url in event.mimeData().urls()
        ):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()


class AttachmentViewer(QFrame):
    """Prévia local com navegação, zoom e rotação de imagens."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("card", True)
        self.images: list[TicketAttachment] = []
        self.current: TicketAttachment | None = None
        self.original_pixmap = QPixmap()
        self.rotation = 0
        self.zoom = 1.0
        self.fit_to_window = True
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 15, 16, 16)
        layout.setSpacing(9)

        header = QHBoxLayout()
        copy = QVBoxLayout()
        copy.setSpacing(1)
        title = QLabel("Visualizador")
        title.setObjectName("sectionTitle")
        self.file_label = QLabel("Selecione uma imagem para visualizar")
        self.file_label.setProperty("muted", True)
        self.file_label.setWordWrap(True)
        copy.addWidget(title)
        copy.addWidget(self.file_label)
        header.addLayout(copy, 1)
        self.open_button = QPushButton("Abrir arquivo")
        self.open_button.setProperty("secondary", True)
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_current)
        header.addWidget(self.open_button)
        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setObjectName("imageScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview = QLabel(
            "As imagens anexadas aparecem aqui.\nDocumentos e logs abrem no programa padrão do Windows."
        )
        self.preview.setObjectName("imagePreview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setWordWrap(True)
        self.preview.setMinimumSize(300, 280)
        self.scroll.setWidget(self.preview)
        layout.addWidget(self.scroll, 1)

        controls = QHBoxLayout()
        controls.setSpacing(6)
        self.previous_button = self._control("‹ Anterior", self.previous_image)
        self.next_button = self._control("Próxima ›", self.next_image)
        controls.addWidget(self.previous_button)
        controls.addWidget(self.next_button)
        controls.addStretch()
        self.zoom_out_button = self._control("−", lambda: self.change_zoom(0.8))
        self.fit_button = self._control("Ajustar", self.fit_image)
        self.zoom_in_button = self._control("+", lambda: self.change_zoom(1.25))
        self.rotate_left_button = self._control("↶", lambda: self.rotate_image(-90))
        self.rotate_right_button = self._control("↷", lambda: self.rotate_image(90))
        controls.addWidget(self.zoom_out_button)
        controls.addWidget(self.fit_button)
        controls.addWidget(self.zoom_in_button)
        controls.addWidget(self.rotate_left_button)
        controls.addWidget(self.rotate_right_button)
        self.position_label = QLabel("Nenhuma imagem")
        self.position_label.setProperty("muted", True)
        controls.addWidget(self.position_label)
        layout.addLayout(controls)
        self._update_controls()

    @staticmethod
    def _control(text: str, callback) -> QPushButton:
        button = QPushButton(text)
        button.setProperty("secondary", True)
        button.clicked.connect(callback)
        return button

    def set_attachments(self, attachments: list[TicketAttachment]) -> None:
        self.images = [item for item in attachments if item.file_type == "image"]
        if self.current and not any(item.id == self.current.id for item in attachments):
            self.clear()
        self._update_controls()

    def show_attachment(self, attachment: TicketAttachment) -> None:
        self.current = attachment
        self.file_label.setText(
            f"{attachment.original_name} · {attachment.type_label} · "
            f"{format_bytes(attachment.size_bytes)}"
        )
        self.open_button.setEnabled(Path(attachment.file_path).exists())
        self.rotation = 0
        self.zoom = 1.0
        self.fit_to_window = True
        if attachment.file_type != "image":
            self.original_pixmap = QPixmap()
            self.preview.setPixmap(QPixmap())
            self.preview.setText(
                "Este arquivo será aberto no programa padrão do Windows.\n\n"
                "Use “Abrir arquivo” ou dê dois cliques na lista."
            )
            self._update_controls()
            return
        pixmap = QPixmap(attachment.file_path)
        if pixmap.isNull():
            self.original_pixmap = QPixmap()
            self.preview.setPixmap(QPixmap())
            self.preview.setText("Não foi possível carregar a prévia desta imagem.")
        else:
            self.original_pixmap = pixmap
            self.preview.setText("")
            self._render()
        self._update_controls()

    def clear(self) -> None:
        self.current = None
        self.original_pixmap = QPixmap()
        self.preview.setPixmap(QPixmap())
        self.preview.setText(
            "As imagens anexadas aparecem aqui.\nDocumentos e logs abrem no programa padrão do Windows."
        )
        self.file_label.setText("Selecione uma imagem para visualizar")
        self.open_button.setEnabled(False)
        self._update_controls()

    def change_zoom(self, factor: float) -> None:
        if self.original_pixmap.isNull():
            return
        self.fit_to_window = False
        self.zoom = max(0.25, min(4.0, self.zoom * factor))
        self._render()

    def fit_image(self) -> None:
        if self.original_pixmap.isNull():
            return
        self.fit_to_window = True
        self._render()

    def rotate_image(self, degrees: int) -> None:
        if self.original_pixmap.isNull():
            return
        self.rotation = (self.rotation + degrees) % 360
        self._render()

    def previous_image(self) -> None:
        self._navigate(-1)

    def next_image(self) -> None:
        self._navigate(1)

    def _navigate(self, step: int) -> None:
        index = self._image_index()
        target = index + step
        if 0 <= target < len(self.images):
            self.show_attachment(self.images[target])

    def open_current(self) -> None:
        if self.current and Path(self.current.file_path).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.current.file_path))

    def _render(self) -> None:
        if self.original_pixmap.isNull():
            return
        transformed = self.original_pixmap.transformed(
            QTransform().rotate(self.rotation),
            Qt.TransformationMode.SmoothTransformation,
        )
        if self.fit_to_window:
            viewport = self.scroll.viewport().size()
            target_width = max(80, viewport.width() - 24)
            target_height = max(80, viewport.height() - 24)
            rendered = transformed.scaled(
                target_width,
                target_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        else:
            rendered = transformed.scaled(
                max(1, int(transformed.width() * self.zoom)),
                max(1, int(transformed.height() * self.zoom)),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self.preview.setPixmap(rendered)
        self.preview.resize(rendered.size())
        self._update_controls()

    def _image_index(self) -> int:
        if not self.current or self.current.file_type != "image":
            return -1
        return next(
            (index for index, item in enumerate(self.images) if item.id == self.current.id),
            -1,
        )

    def _update_controls(self) -> None:
        has_image = not self.original_pixmap.isNull()
        for button in (
            self.zoom_out_button,
            self.fit_button,
            self.zoom_in_button,
            self.rotate_left_button,
            self.rotate_right_button,
        ):
            button.setEnabled(has_image)
        index = self._image_index()
        self.previous_button.setEnabled(index > 0)
        self.next_button.setEnabled(index >= 0 and index < len(self.images) - 1)
        if index >= 0:
            zoom_text = "ajustada" if self.fit_to_window else f"{self.zoom * 100:.0f}%"
            self.position_label.setText(
                f"Imagem {index + 1} de {len(self.images)} · {zoom_text} · {self.rotation}°"
            )
        else:
            self.position_label.setText(
                f"{len(self.images)} imagem(ns)" if self.images else "Nenhuma imagem"
            )

    def resizeEvent(self, event: QEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.fit_to_window and not self.original_pixmap.isNull():
            self._render()


class AttachmentsPage(QWidget):
    attachments_changed = Signal(int)

    def __init__(
        self,
        ticket_service: TicketService,
        attachment_service: AttachmentService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.ticket_service = ticket_service
        self.attachment_service = attachment_service
        self.records: dict[int, TicketAttachment] = {}
        self._build_ui()
        self.refresh_tickets()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 22, 30, 28)
        layout.setSpacing(12)

        heading = QFrame()
        heading.setProperty("card", True)
        heading_layout = QHBoxLayout(heading)
        heading_layout.setContentsMargins(18, 14, 18, 14)
        copy = QVBoxLayout()
        copy.setSpacing(2)
        title = QLabel("Arquivos e evidências")
        title.setObjectName("sectionTitle")
        detail = QLabel("Tudo fica armazenado localmente e organizado pelo protocolo.")
        detail.setProperty("muted", True)
        copy.addWidget(title)
        copy.addWidget(detail)
        heading_layout.addLayout(copy, 1)
        self.ticket_combo = QComboBox()
        self.ticket_combo.setMinimumWidth(300)
        self.ticket_combo.currentIndexChanged.connect(self._ticket_changed)
        heading_layout.addWidget(self.ticket_combo)
        self.folder_button = QPushButton("Abrir pasta")
        self.folder_button.setProperty("secondary", True)
        self.folder_button.clicked.connect(self._open_folder)
        heading_layout.addWidget(self.folder_button)
        self.add_button = QPushButton("Adicionar arquivos")
        self.add_button.setProperty("primary", True)
        self.add_button.clicked.connect(self._choose_files)
        heading_layout.addWidget(self.add_button)
        layout.addWidget(heading)

        self.status_label = QLabel("Selecione um chamado para gerenciar seus arquivos.")
        self.status_label.setObjectName("privacyNotice")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self._build_files_card(), 1)
        self.viewer = AttachmentViewer()
        body.addWidget(self.viewer, 2)
        layout.addLayout(body, 1)

    def _build_files_card(self) -> QWidget:
        card = QFrame()
        card.setProperty("card", True)
        card.setMinimumWidth(340)
        card.setMaximumWidth(470)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 15, 16, 16)
        layout.setSpacing(9)
        row = QHBoxLayout()
        title = QLabel("Arquivos do chamado")
        title.setObjectName("sectionTitle")
        self.count_label = QLabel("0 arquivos")
        self.count_label.setObjectName("countBadge")
        row.addWidget(title)
        row.addStretch()
        row.addWidget(self.count_label)
        layout.addLayout(row)

        self.drop_zone = FileDropZone()
        self.drop_zone.files_dropped.connect(self._add_files)
        layout.addWidget(self.drop_zone)

        self.files_list = QListWidget()
        self.files_list.setObjectName("attachmentList")
        self.files_list.setAlternatingRowColors(True)
        self.files_list.currentItemChanged.connect(self._selection_changed)
        self.files_list.itemDoubleClicked.connect(self._item_activated)
        layout.addWidget(self.files_list, 1)
        tip = QLabel("Dê dois cliques em documentos e logs para abri-los.")
        tip.setProperty("muted", True)
        tip.setWordWrap(True)
        layout.addWidget(tip)
        return card

    def refresh_tickets(self, select_id: int | None = None) -> None:
        previous = select_id or self.ticket_combo.currentData()
        self.ticket_combo.blockSignals(True)
        self.ticket_combo.clear()
        self.ticket_combo.addItem("Selecione um chamado...", None)
        for ticket in self.ticket_service.list_all():
            self.ticket_combo.addItem(f"{ticket.protocol} — {ticket.title}", ticket.id)
        if previous:
            index = self.ticket_combo.findData(previous)
            self.ticket_combo.setCurrentIndex(index if index >= 0 else 0)
        self.ticket_combo.blockSignals(False)
        self._ticket_changed()

    def selected_ticket(self) -> Ticket | None:
        ticket_id = self.ticket_combo.currentData()
        return self.ticket_service.get(int(ticket_id)) if ticket_id else None

    def refresh_attachments(self, select_id: int | None = None) -> None:
        ticket = self.selected_ticket()
        self.files_list.clear()
        self.records.clear()
        records = self.attachment_service.list_for_ticket(ticket.id) if ticket else []
        for record in records:
            self.records[record.id] = record
            icon = {"image": "▧", "document": "▤", "log": "≡"}.get(
                record.file_type, "•"
            )
            item = QListWidgetItem(
                f"{icon}  {record.original_name}\n"
                f"{record.type_label} · {format_bytes(record.size_bytes)} · {record.created_at}"
            )
            item.setData(Qt.ItemDataRole.UserRole, record.id)
            item.setToolTip(record.file_path)
            self.files_list.addItem(item)
            if record.id == select_id:
                self.files_list.setCurrentItem(item)
        self.count_label.setText(f"{len(records)} arquivo(s)")
        self.viewer.set_attachments(records)
        if not select_id:
            self.viewer.clear()
        if ticket:
            self.status_label.setText(
                f"Arquivos de {ticket.protocol} · imagens, documentos e logs permanecem locais."
            )
        else:
            self.status_label.setText("Selecione um chamado para gerenciar seus arquivos.")

    def _ticket_changed(self, *_args) -> None:
        enabled = self.selected_ticket() is not None
        self.add_button.setEnabled(enabled)
        self.folder_button.setEnabled(enabled)
        self.drop_zone.setEnabled(enabled)
        self.refresh_attachments()

    def _choose_files(self) -> None:
        paths, _selected_filter = QFileDialog.getOpenFileNames(
            self,
            "Adicionar arquivos ao chamado",
            "",
            "Arquivos suportados (*.bmp *.gif *.jpeg *.jpg *.png *.webp *.csv *.doc "
            "*.docx *.odt *.pdf *.ppt *.pptx *.rtf *.xls *.xlsx *.zip *.ini *.json "
            "*.log *.txt *.xml *.yaml *.yml)",
        )
        if paths:
            self._add_files(paths)

    def _add_files(self, paths: list[str]) -> None:
        ticket = self.selected_ticket()
        if not ticket:
            QMessageBox.information(
                self, "Selecione um chamado", "Escolha o chamado que receberá os arquivos."
            )
            return
        try:
            attached = self.attachment_service.attach_many(ticket, paths)
        except (AttachmentValidationError, OSError) as error:
            self.refresh_attachments()
            QMessageBox.warning(self, "Não foi possível anexar", str(error))
            return
        except Exception as error:
            self.refresh_attachments()
            QMessageBox.critical(self, "Falha ao anexar", str(error))
            return
        last_id = attached[-1].id
        self.refresh_attachments(last_id)
        self.status_label.setText(
            f"{len(attached)} arquivo(s) anexado(s) localmente a {ticket.protocol}."
        )
        self.attachments_changed.emit(ticket.id)

    def _selection_changed(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if not current:
            return
        record = self.records.get(int(current.data(Qt.ItemDataRole.UserRole)))
        if record:
            self.viewer.show_attachment(record)

    def _item_activated(self, item: QListWidgetItem) -> None:
        record = self.records.get(int(item.data(Qt.ItemDataRole.UserRole)))
        if record and record.file_type != "image":
            self.viewer.show_attachment(record)
            self.viewer.open_current()

    def _open_folder(self) -> None:
        ticket = self.selected_ticket()
        if not ticket:
            return
        folders = self.attachment_service.ensure_ticket_folders(ticket.protocol)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folders["image"].parent)))
