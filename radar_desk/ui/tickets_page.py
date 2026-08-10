"""Tela de cadastro e administração local de chamados."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from radar_desk.models.ticket import Ticket
from radar_desk.services.ticket_service import TicketService, TicketValidationError
from radar_desk.ui.ticket_dialog import TicketDialog


class TicketsPage(QWidget):
    tickets_changed = Signal()

    def __init__(self, service: TicketService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.tickets: dict[int, Ticket] = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 30)
        layout.setSpacing(14)

        toolbar = QFrame()
        toolbar.setProperty("card", True)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(18, 14, 18, 14)
        toolbar_layout.setSpacing(14)

        copy = QVBoxLayout()
        copy.setSpacing(2)
        title = QLabel("Chamados locais")
        title.setObjectName("sectionTitle")
        caption = QLabel("Todos os registros são salvos neste computador.")
        caption.setProperty("muted", True)
        copy.addWidget(title)
        copy.addWidget(caption)
        toolbar_layout.addLayout(copy, 1)

        self.total_label = QLabel("0 chamados")
        self.total_label.setObjectName("countBadge")
        toolbar_layout.addWidget(self.total_label)

        new_button = QPushButton("＋  Novo chamado")
        new_button.setProperty("primary", True)
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_button.clicked.connect(self._create_ticket)
        toolbar_layout.addWidget(new_button)
        layout.addWidget(toolbar)

        content = QHBoxLayout()
        content.setSpacing(14)

        list_card = QFrame()
        list_card.setProperty("card", True)
        list_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(1, 1, 1, 1)

        self.list_stack = QStackedWidget()
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ("Protocolo", "Título", "Categoria", "Prioridade", "Status", "Atualizado")
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(46)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._show_selection)
        self.table.itemDoubleClicked.connect(lambda _item: self._edit_selected())
        self.list_stack.addWidget(self.table)

        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        empty_layout.setContentsMargins(30, 50, 30, 50)
        empty_layout.addStretch()
        empty_icon = QLabel("◎")
        empty_icon.setObjectName("emptyIcon")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_title = QLabel("Nenhum chamado cadastrado")
        empty_title.setObjectName("emptyTitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_text = QLabel("Crie o primeiro chamado para começar a usar o Radar Desk.")
        empty_text.setProperty("muted", True)
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_text)
        empty_layout.addStretch()
        self.list_stack.addWidget(empty)
        list_layout.addWidget(self.list_stack)
        content.addWidget(list_card, 3)

        detail = QFrame()
        detail.setProperty("card", True)
        detail.setMinimumWidth(290)
        detail.setMaximumWidth(370)
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(20, 20, 20, 20)
        detail_layout.setSpacing(10)
        detail_heading = QLabel("Detalhes")
        detail_heading.setObjectName("sectionTitle")
        detail_layout.addWidget(detail_heading)

        self.detail_protocol = QLabel("Selecione um chamado")
        self.detail_protocol.setObjectName("detailProtocol")
        self.detail_title = QLabel("—")
        self.detail_title.setObjectName("detailTitle")
        self.detail_title.setWordWrap(True)
        self.detail_meta = QLabel()
        self.detail_meta.setProperty("muted", True)
        self.detail_meta.setWordWrap(True)
        self.detail_description = QLabel(
            "Os dados completos do chamado selecionado aparecerão aqui."
        )
        self.detail_description.setObjectName("detailDescription")
        self.detail_description.setWordWrap(True)
        self.detail_dates = QLabel()
        self.detail_dates.setProperty("muted", True)
        self.detail_dates.setWordWrap(True)
        detail_layout.addWidget(self.detail_protocol)
        detail_layout.addWidget(self.detail_title)
        detail_layout.addWidget(self.detail_meta)
        detail_layout.addSpacing(6)
        detail_layout.addWidget(self.detail_description)
        detail_layout.addStretch()
        detail_layout.addWidget(self.detail_dates)

        actions = QHBoxLayout()
        self.edit_button = QPushButton("Editar")
        self.edit_button.setProperty("secondary", True)
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self._edit_selected)
        self.delete_button = QPushButton("Excluir")
        self.delete_button.setProperty("danger", True)
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._delete_selected)
        actions.addWidget(self.edit_button)
        actions.addWidget(self.delete_button)
        detail_layout.addLayout(actions)
        content.addWidget(detail, 1)
        layout.addLayout(content, 1)

    def refresh(self, select_id: int | None = None) -> None:
        tickets = self.service.list_all()
        self.tickets = {ticket.id: ticket for ticket in tickets}
        self.table.setRowCount(len(tickets))
        for row, ticket in enumerate(tickets):
            values = (
                ticket.protocol,
                ticket.title,
                ticket.category,
                ticket.priority,
                ticket.status,
                Ticket.format_datetime(ticket.updated_at),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, ticket.id)
                if column == 3:
                    self._color_priority(item, ticket.priority)
                if column == 4:
                    self._color_status(item, ticket.status)
                self.table.setItem(row, column, item)

        self.total_label.setText(
            "1 chamado" if len(tickets) == 1 else f"{len(tickets)} chamados"
        )
        self.list_stack.setCurrentIndex(0 if tickets else 1)
        if select_id is not None:
            self.select_ticket(select_id)
        elif tickets:
            self.table.selectRow(0)
        else:
            self._clear_details()

    def select_ticket(self, ticket_id: int) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == ticket_id:
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                return

    def selected_ticket(self) -> Ticket | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.table.item(rows[0].row(), 0)
        ticket_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        return self.tickets.get(ticket_id)

    def _show_selection(self) -> None:
        ticket = self.selected_ticket()
        if not ticket:
            self._clear_details()
            return
        self.detail_protocol.setText(ticket.protocol)
        self.detail_title.setText(ticket.title)
        self.detail_meta.setText(
            f"{ticket.category}  •  {ticket.priority}  •  {ticket.status}"
        )
        self.detail_description.setText(ticket.description)
        self.detail_dates.setText(
            f"Aberto em {Ticket.format_datetime(ticket.created_at)}\n"
            f"Atualizado em {Ticket.format_datetime(ticket.updated_at)}"
        )
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)

    def _clear_details(self) -> None:
        self.table.clearSelection()
        self.detail_protocol.setText("Selecione um chamado")
        self.detail_title.setText("—")
        self.detail_meta.clear()
        self.detail_description.setText(
            "Os dados completos do chamado selecionado aparecerão aqui."
        )
        self.detail_dates.clear()
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def _create_ticket(self) -> None:
        dialog = TicketDialog(parent=self)
        if dialog.exec() != TicketDialog.DialogCode.Accepted:
            return
        try:
            ticket = self.service.create(dialog.value())
        except TicketValidationError as error:
            QMessageBox.warning(self, "Dados inválidos", str(error))
            return
        self.refresh(ticket.id)
        self.tickets_changed.emit()

    def _edit_selected(self) -> None:
        ticket = self.selected_ticket()
        if not ticket:
            return
        dialog = TicketDialog(ticket, self)
        if dialog.exec() != TicketDialog.DialogCode.Accepted:
            return
        try:
            updated = self.service.update(ticket.id, dialog.value())
        except TicketValidationError as error:
            QMessageBox.warning(self, "Dados inválidos", str(error))
            return
        self.refresh(updated.id)
        self.tickets_changed.emit()

    def _delete_selected(self) -> None:
        ticket = self.selected_ticket()
        if not ticket:
            return
        answer = QMessageBox.question(
            self,
            "Excluir chamado",
            f"Deseja excluir permanentemente o chamado {ticket.protocol}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.service.delete(ticket.id)
        self.refresh()
        self.tickets_changed.emit()

    @staticmethod
    def _color_priority(item: QTableWidgetItem, priority: str) -> None:
        colors = {
            "Baixa": ("#d1fae5", "#047857"),
            "Média": ("#dbeafe", "#1d4ed8"),
            "Alta": ("#fef3c7", "#b45309"),
            "Crítica": ("#fee2e2", "#b91c1c"),
        }
        background, foreground = colors.get(priority, ("#e2e8f0", "#334155"))
        item.setBackground(QColor(background))
        item.setForeground(QColor(foreground))

    @staticmethod
    def _color_status(item: QTableWidgetItem, status: str) -> None:
        colors = {
            "Aberto": ("#ccfbf1", "#0f766e"),
            "Em andamento": ("#dbeafe", "#1d4ed8"),
            "Aguardando": ("#fef3c7", "#a16207"),
            "Resolvido": ("#e2e8f0", "#475569"),
        }
        background, foreground = colors.get(status, ("#e2e8f0", "#334155"))
        item.setBackground(QColor(background))
        item.setForeground(QColor(foreground))
