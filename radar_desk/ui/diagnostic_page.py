"""Tela de coleta, consentimento e anexo de diagnóstico."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from radar_desk.models.diagnostic import DiagnosticSnapshot
from radar_desk.models.ticket import Ticket
from radar_desk.services.diagnostic_service import DiagnosticService
from radar_desk.services.ticket_service import TicketService


class DiagnosticWorker(QThread):
    snapshot_ready = Signal(object)
    failed = Signal(str)

    def __init__(self, service: DiagnosticService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service

    def run(self) -> None:
        try:
            self.snapshot_ready.emit(self.service.collect())
        except Exception as error:  # limite seguro da thread
            self.failed.emit(str(error))


class DiagnosticPage(QWidget):
    diagnostic_attached = Signal(int)

    def __init__(
        self,
        ticket_service: TicketService,
        diagnostic_service: DiagnosticService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.ticket_service = ticket_service
        self.diagnostic_service = diagnostic_service
        self.snapshot: DiagnosticSnapshot | None = None
        self.screenshot: QPixmap | None = None
        self.worker: DiagnosticWorker | None = None
        self._build_ui()
        self.refresh_tickets()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 22, 30, 28)
        layout.setSpacing(12)

        heading_card = QFrame()
        heading_card.setProperty("card", True)
        heading_layout = QHBoxLayout(heading_card)
        heading_layout.setContentsMargins(18, 14, 18, 14)
        heading_layout.setSpacing(12)
        copy = QVBoxLayout()
        copy.setSpacing(2)
        title = QLabel("Diagnóstico transparente")
        title.setObjectName("sectionTitle")
        caption = QLabel(
            "Os dados permanecem locais e só são anexados após sua confirmação."
        )
        caption.setProperty("muted", True)
        copy.addWidget(title)
        copy.addWidget(caption)
        heading_layout.addLayout(copy, 1)

        self.ticket_combo = QComboBox()
        self.ticket_combo.setMinimumWidth(280)
        self.ticket_combo.currentIndexChanged.connect(self._ticket_changed)
        heading_layout.addWidget(self.ticket_combo)
        self.collect_button = QPushButton("Coletar diagnóstico")
        self.collect_button.setProperty("primary", True)
        self.collect_button.clicked.connect(self._collect)
        heading_layout.addWidget(self.collect_button)
        layout.addWidget(heading_card)

        self.status_label = QLabel(
            "Selecione um chamado. A coleta mostrará todos os dados antes do anexo."
        )
        self.status_label.setObjectName("privacyNotice")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self._build_data_card(), 2)
        body.addWidget(self._build_evidence_card(), 1)
        layout.addLayout(body, 1)

    def _build_data_card(self) -> QWidget:
        card = QFrame()
        card.setProperty("card", True)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 15, 16, 16)
        title = QLabel("Dados que serão anexados")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        subtitle = QLabel("Nenhum dado foi coletado ainda.")
        subtitle.setProperty("muted", True)
        self.data_subtitle = subtitle
        layout.addWidget(subtitle)

        self.data_table = QTableWidget(0, 2)
        self.data_table.setHorizontalHeaderLabels(("Informação", "Valor coletado"))
        self.data_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.data_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.data_table.verticalHeader().hide()
        self.data_table.verticalHeader().setDefaultSectionSize(36)
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.data_table, 1)
        return card

    def _build_evidence_card(self) -> QWidget:
        card = QFrame()
        card.setProperty("card", True)
        card.setMinimumWidth(330)
        card.setMaximumWidth(430)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 15, 16, 16)
        layout.setSpacing(9)

        title = QLabel("Captura de tela opcional")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        notice = QLabel(
            "A tela inteira pode conter informações pessoais. Ela nunca será capturada "
            "sem uma autorização específica."
        )
        notice.setProperty("muted", True)
        notice.setWordWrap(True)
        layout.addWidget(notice)

        self.screenshot_label = QLabel("Nenhuma captura incluída")
        self.screenshot_label.setObjectName("screenshotPreview")
        self.screenshot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screenshot_label.setMinimumHeight(150)
        self.screenshot_label.setWordWrap(True)
        layout.addWidget(self.screenshot_label)

        self.capture_button = QPushButton("Autorizar e capturar tela")
        self.capture_button.setProperty("secondary", True)
        self.capture_button.setEnabled(False)
        self.capture_button.clicked.connect(self._capture_screen)
        layout.addWidget(self.capture_button)

        attachments_title = QLabel("Diagnósticos já anexados")
        attachments_title.setStyleSheet("font-weight: 700;")
        layout.addWidget(attachments_title)
        self.attachments_list = QListWidget()
        self.attachments_list.setObjectName("interactionList")
        self.attachments_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.attachments_list.setMaximumHeight(120)
        layout.addWidget(self.attachments_list)

        self.attach_button = QPushButton("Anexar ao chamado selecionado")
        self.attach_button.setProperty("primary", True)
        self.attach_button.setEnabled(False)
        self.attach_button.clicked.connect(self._attach)
        layout.addWidget(self.attach_button)
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

    def _ticket_changed(self, *_args) -> None:
        ticket = self.selected_ticket()
        self.collect_button.setEnabled(ticket is not None and self.worker is None)
        self.attach_button.setEnabled(ticket is not None and self.snapshot is not None)
        self._refresh_attachments(ticket.id if ticket else None)

    def _collect(self) -> None:
        ticket = self.selected_ticket()
        if not ticket:
            QMessageBox.information(
                self,
                "Selecione um chamado",
                "Escolha o chamado que receberá o diagnóstico antes de coletar.",
            )
            return
        self.collect_button.setEnabled(False)
        self.capture_button.setEnabled(False)
        self.attach_button.setEnabled(False)
        self.status_label.setText(
            "Coletando informações locais e executando um ping para 1.1.1.1..."
        )
        self.worker = DiagnosticWorker(self.diagnostic_service, self)
        self.worker.snapshot_ready.connect(self._show_snapshot)
        self.worker.failed.connect(self._collection_failed)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _show_snapshot(self, snapshot: DiagnosticSnapshot) -> None:
        self.snapshot = snapshot
        self.screenshot = None
        self.screenshot_label.setPixmap(QPixmap())
        self.screenshot_label.setText("Nenhuma captura incluída")
        items = snapshot.display_items()
        self.data_table.setRowCount(len(items))
        for row, (label, value) in enumerate(items):
            label_item = QTableWidgetItem(label)
            label_item.setForeground(Qt.GlobalColor.darkGray)
            self.data_table.setItem(row, 0, label_item)
            self.data_table.setItem(row, 1, QTableWidgetItem(value))
        self.data_subtitle.setText(
            f"Revise os {len(items)} campos abaixo. Nada foi anexado ainda."
        )
        self.status_label.setText(
            "Coleta concluída. Confira exatamente os dados abaixo antes de anexar."
        )
        self.capture_button.setEnabled(True)
        self.attach_button.setEnabled(self.selected_ticket() is not None)

    def _collection_failed(self, message: str) -> None:
        self.status_label.setText("Não foi possível concluir a coleta.")
        QMessageBox.critical(self, "Falha no diagnóstico", message)

    def _worker_finished(self) -> None:
        worker = self.worker
        self.worker = None
        if worker:
            worker.deleteLater()
        self.collect_button.setEnabled(self.selected_ticket() is not None)

    def _capture_screen(self) -> None:
        answer = QMessageBox.question(
            self,
            "Autorizar captura de tela",
            "A captura incluirá toda a tela principal visível neste momento e poderá "
            "conter dados pessoais ou confidenciais.\n\nDeseja autorizar a captura agora?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        screen = QApplication.primaryScreen()
        if not screen:
            QMessageBox.warning(self, "Captura indisponível", "Nenhuma tela foi detectada.")
            return
        self.screenshot = screen.grabWindow(0)
        self._render_screenshot()
        self.capture_button.setText("Capturar novamente")
        self.status_label.setText(
            "Captura autorizada e incluída na prévia. Revise-a antes de anexar."
        )

    def _render_screenshot(self) -> None:
        if not self.screenshot:
            return
        target = self.screenshot_label.size()
        preview = self.screenshot.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.screenshot_label.setPixmap(preview)

    def resizeEvent(self, event) -> None:  # noqa: N802 - API Qt
        super().resizeEvent(event)
        self._render_screenshot()

    def _attach(self) -> None:
        ticket = self.selected_ticket()
        if not ticket or not self.snapshot:
            return
        screenshot_text = "com captura de tela" if self.screenshot else "sem captura de tela"
        answer = QMessageBox.question(
            self,
            "Confirmar anexo",
            f"Serão anexados {len(self.snapshot.display_items())} campos {screenshot_text} "
            f"ao chamado {ticket.protocol}.\n\nNada será enviado para a internet. Confirmar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            attached = self.diagnostic_service.attach(
                ticket,
                self.snapshot,
                self._screenshot_bytes(),
            )
        except Exception as error:
            QMessageBox.critical(self, "Falha ao anexar", str(error))
            return
        self._refresh_attachments(ticket.id)
        self.status_label.setText(
            f"Diagnóstico anexado localmente ao chamado {ticket.protocol}."
        )
        self.diagnostic_attached.emit(ticket.id)
        QMessageBox.information(
            self,
            "Diagnóstico anexado",
            f"Relatório salvo em:\n{attached.report_path}",
        )

    def _screenshot_bytes(self) -> bytes | None:
        if not self.screenshot:
            return None
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        self.screenshot.save(buffer, "PNG")
        buffer.close()
        return bytes(data)

    def _refresh_attachments(self, ticket_id: int | None) -> None:
        self.attachments_list.clear()
        if not ticket_id:
            self.attachments_list.addItem("Selecione um chamado.")
            return
        records = self.diagnostic_service.list_for_ticket(ticket_id)
        if not records:
            self.attachments_list.addItem("Nenhum diagnóstico anexado.")
            return
        for record in records:
            screenshot = " • captura incluída" if record.screenshot_path else ""
            item = QListWidgetItem(f"{record.created_at}{screenshot}\n{record.report_path}")
            self.attachments_list.addItem(item)
