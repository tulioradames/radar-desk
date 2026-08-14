"""Painel de indicadores, avaliações e exportações operacionais."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QDate, Signal, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from radar_desk.models.report import ReportFilter, ReportSnapshot
from radar_desk.models.ticket import Ticket
from radar_desk.services.report_service import ReportService, ReportValidationError
from radar_desk.ui.widgets import StatCard


class ReportsPage(QWidget):
    reports_changed = Signal()

    def __init__(self, service: ReportService) -> None:
        super().__init__()
        self.service = service
        self.current_snapshot: ReportSnapshot | None = None
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 24, 30, 30)
        layout.setSpacing(16)

        layout.addWidget(self._build_filter_card())

        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.total_card = StatCard("Chamados no período", "0", "#2dd4bf")
        self.active_card = StatCard("Chamados ativos", "0", "#60a5fa")
        self.overdue_card = StatCard("SLA atrasado", "0", "#fb7185")
        self.time_card = StatCard("Tempo médio", "—", "#f59e0b")
        self.rating_card = StatCard("Avaliação média", "—", "#a78bfa")
        for card in (
            self.total_card,
            self.active_card,
            self.overdue_card,
            self.time_card,
            self.rating_card,
        ):
            stats.addWidget(card)
        layout.addLayout(stats)

        breakdown_row = QHBoxLayout()
        breakdown_row.setSpacing(16)
        self.status_table = self._summary_table()
        self.category_table = self._summary_table()
        breakdown_row.addWidget(
            self._table_card("Chamados por status", self.status_table), 1
        )
        breakdown_row.addWidget(
            self._table_card("Chamados por categoria", self.category_table), 1
        )
        layout.addLayout(breakdown_row)

        operations_row = QHBoxLayout()
        operations_row.setSpacing(16)
        self.volume_table = self._summary_table()
        self.volume_table.setHorizontalHeaderLabels(["Data", "Abertos"])
        self.overdue_table = QTableWidget(0, 5)
        self.overdue_table.setHorizontalHeaderLabels(
            ["Protocolo", "Título", "Prioridade", "Status", "Responsável"]
        )
        self._configure_table(self.overdue_table)
        self.overdue_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        operations_row.addWidget(
            self._table_card("Volume por período", self.volume_table), 1
        )
        operations_row.addWidget(
            self._table_card("Chamados atrasados", self.overdue_table), 2
        )
        layout.addLayout(operations_row)

        layout.addWidget(self._build_rating_card())
        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _build_filter_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        layout = QGridLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        copy = QVBoxLayout()
        copy.setSpacing(2)
        title = QLabel("Relatório operacional")
        title.setObjectName("sectionTitle")
        detail = QLabel("Analise todos os dados ou delimite um período de abertura.")
        detail.setProperty("muted", True)
        copy.addWidget(title)
        copy.addWidget(detail)
        layout.addLayout(copy, 0, 0, 1, 7)

        self.period_check = QCheckBox("Filtrar período")
        self.period_check.toggled.connect(self._toggle_period)
        layout.addWidget(self.period_check, 1, 0)
        self.start_date = QDateEdit(QDate.currentDate().addDays(-29))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        self.start_date.setEnabled(False)
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd/MM/yyyy")
        self.end_date.setEnabled(False)
        layout.addWidget(self.start_date, 1, 1)
        layout.addWidget(self.end_date, 1, 2)
        layout.setColumnStretch(3, 1)

        refresh_button = QPushButton("Atualizar")
        refresh_button.setProperty("secondary", True)
        refresh_button.clicked.connect(self.refresh)
        layout.addWidget(refresh_button, 1, 4)
        excel_button = QPushButton("Exportar Excel")
        excel_button.setProperty("primary", True)
        excel_button.clicked.connect(self._export_excel)
        layout.addWidget(excel_button, 1, 5)
        pdf_button = QPushButton("Exportar PDF")
        pdf_button.setProperty("secondary", True)
        pdf_button.clicked.connect(self._export_pdf)
        layout.addWidget(pdf_button, 1, 6)
        return card

    def _build_rating_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(10)
        title = QLabel("Avaliação do atendimento")
        title.setObjectName("sectionTitle")
        detail = QLabel(
            "Registre de 1 a 5 estrelas para chamados resolvidos ou encerrados. "
            "Uma nova avaliação substitui a anterior do mesmo protocolo."
        )
        detail.setProperty("muted", True)
        detail.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(detail)

        fields = QHBoxLayout()
        fields.setSpacing(10)
        self.rating_ticket = QComboBox()
        self.rating_ticket.setMinimumWidth(300)
        self.rating_ticket.currentIndexChanged.connect(self._load_rating)
        self.rating_score = QComboBox()
        for score in range(1, 6):
            self.rating_score.addItem(f"{'★' * score}{'☆' * (5 - score)}  {score}/5", score)
        self.rating_score.setCurrentIndex(4)
        self.rating_comment = QTextEdit()
        self.rating_comment.setPlaceholderText("Comentário opcional sobre o atendimento")
        self.rating_comment.setMaximumHeight(74)
        save_button = QPushButton("Salvar avaliação")
        save_button.setProperty("primary", True)
        save_button.clicked.connect(self._save_rating)
        self.rating_save_button = save_button
        fields.addWidget(self.rating_ticket, 2)
        fields.addWidget(self.rating_score, 1)
        fields.addWidget(self.rating_comment, 3)
        fields.addWidget(save_button)
        layout.addLayout(fields)
        self.rating_hint = QLabel()
        self.rating_hint.setProperty("muted", True)
        layout.addWidget(self.rating_hint)
        return card

    @staticmethod
    def _table_card(title: str, table: QTableWidget) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(10)
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)
        layout.addWidget(table)
        return card

    def _summary_table(self) -> QTableWidget:
        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels(["Indicador", "Quantidade"])
        self._configure_table(table)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(225)
        return table

    @staticmethod
    def _configure_table(table: QTableWidget) -> None:
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)

    def refresh(self, *_args) -> None:
        try:
            snapshot = self.service.build(self._filters())
        except ReportValidationError as error:
            QMessageBox.warning(self, "Período inválido", str(error))
            return
        self.current_snapshot = snapshot
        self.total_card.set_value(str(snapshot.total))
        self.active_card.set_value(str(snapshot.active))
        self.overdue_card.set_value(str(snapshot.overdue))
        self.time_card.set_value(self._hours_label(snapshot.average_resolution_hours))
        self.rating_card.set_value(self._rating_label(snapshot))
        self._fill_summary(self.status_table, snapshot.status_counts)
        self._fill_summary(self.category_table, snapshot.category_counts)
        self._fill_volume(snapshot.volume_by_day)
        self._fill_overdue(snapshot.overdue_tickets)
        self._refresh_rating_tickets(snapshot.tickets)

    def _filters(self) -> ReportFilter:
        if not self.period_check.isChecked():
            return ReportFilter()
        return ReportFilter(
            start_date=self.start_date.date().toString("yyyy-MM-dd"),
            end_date=self.end_date.date().toString("yyyy-MM-dd"),
        )

    @staticmethod
    def _fill_summary(
        table: QTableWidget,
        values: tuple[tuple[str, int], ...],
    ) -> None:
        table.setRowCount(len(values))
        for row, (label, total) in enumerate(values):
            table.setItem(row, 0, QTableWidgetItem(label))
            item = QTableWidgetItem(str(total))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 1, item)

    def _fill_volume(self, values: tuple[tuple[str, int], ...]) -> None:
        recent = values[-31:]
        self.volume_table.setRowCount(len(recent))
        for row, (day, total) in enumerate(recent):
            parsed = QDate.fromString(day, "yyyy-MM-dd")
            label = parsed.toString("dd/MM/yyyy") if parsed.isValid() else day
            self.volume_table.setItem(row, 0, QTableWidgetItem(label))
            item = QTableWidgetItem(str(total))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.volume_table.setItem(row, 1, item)

    def _fill_overdue(self, tickets: tuple[Ticket, ...]) -> None:
        self.overdue_table.setRowCount(len(tickets))
        for row, ticket in enumerate(tickets):
            values = (
                ticket.protocol,
                ticket.title,
                ticket.priority,
                ticket.status,
                ticket.assignee or "Não atribuído",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setForeground(QColor("#be123c"))
                self.overdue_table.setItem(row, column, item)

    def _refresh_rating_tickets(self, tickets: tuple[Ticket, ...]) -> None:
        selected_id = self.rating_ticket.currentData()
        eligible = [
            ticket for ticket in tickets if ticket.status in ("Resolvido", "Encerrado")
        ]
        self.rating_ticket.blockSignals(True)
        self.rating_ticket.clear()
        if not eligible:
            self.rating_ticket.addItem("Nenhum chamado concluído no período", None)
        else:
            for ticket in eligible:
                self.rating_ticket.addItem(
                    f"{ticket.protocol} · {ticket.title}", ticket.id
                )
        if selected_id is not None:
            index = self.rating_ticket.findData(selected_id)
            if index >= 0:
                self.rating_ticket.setCurrentIndex(index)
        self.rating_ticket.blockSignals(False)
        enabled = bool(eligible)
        self.rating_score.setEnabled(enabled)
        self.rating_comment.setEnabled(enabled)
        self.rating_save_button.setEnabled(enabled)
        self._load_rating()

    def _load_rating(self, *_args) -> None:
        ticket_id = self.rating_ticket.currentData()
        if ticket_id is None:
            self.rating_hint.setText("Conclua um chamado para registrar a avaliação.")
            self.rating_comment.clear()
            return
        rating = self.service.repository.get_rating(int(ticket_id))
        if rating:
            self.rating_score.setCurrentIndex(rating.rating - 1)
            self.rating_comment.setPlainText(rating.comment)
            self.rating_hint.setText("Este chamado já possui avaliação. Salvar atualizará o registro.")
        else:
            self.rating_score.setCurrentIndex(4)
            self.rating_comment.clear()
            self.rating_hint.setText("Ainda não há avaliação para este chamado.")

    def _save_rating(self) -> None:
        ticket_id = self.rating_ticket.currentData()
        if ticket_id is None:
            return
        try:
            self.service.rate_ticket(
                int(ticket_id),
                int(self.rating_score.currentData()),
                self.rating_comment.toPlainText(),
            )
        except ReportValidationError as error:
            QMessageBox.warning(self, "Avaliação inválida", str(error))
            return
        self.refresh()
        self.reports_changed.emit()
        QMessageBox.information(self, "Avaliação salva", "A avaliação foi registrada localmente.")

    def _toggle_period(self, enabled: bool) -> None:
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)
        self.refresh()

    def _export_excel(self) -> None:
        if not self.current_snapshot:
            return
        suggested = str(Path.home() / "RadarDesk-relatorio.xlsx")
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar relatório para Excel", suggested, "Planilha Excel (*.xlsx)"
        )
        if path:
            self._run_export("Excel", self.service.export_excel, path)

    def _export_pdf(self) -> None:
        if not self.current_snapshot:
            return
        suggested = str(Path.home() / "RadarDesk-relatorio.pdf")
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar relatório em PDF", suggested, "Documento PDF (*.pdf)"
        )
        if path:
            self._run_export("PDF", self.service.export_pdf, path)

    def _run_export(self, label: str, exporter, path: str) -> None:
        try:
            saved = exporter(self.current_snapshot, path)
        except Exception as error:  # proteção da fronteira da interface
            QMessageBox.critical(self, "Falha na exportação", str(error))
            return
        QMessageBox.information(
            self,
            f"Relatório {label} criado",
            f"Arquivo salvo em:\n{saved}",
        )

    @staticmethod
    def _hours_label(value: float | None) -> str:
        return f"{value:.1f} h" if value is not None else "—"

    @staticmethod
    def _rating_label(snapshot: ReportSnapshot) -> str:
        return (
            f"{snapshot.average_rating:.1f}/5"
            if snapshot.average_rating is not None
            else "—"
        )
