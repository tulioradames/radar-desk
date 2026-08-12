"""Central operacional para busca, atendimento e interação com chamados."""

from __future__ import annotations

from PySide6.QtCore import QDate, QSize, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from radar_desk.models.ticket import (
    CATEGORIES,
    PRIORITIES,
    STATUSES,
    Ticket,
    TicketFilter,
)
from radar_desk.services.ticket_service import TicketService, TicketValidationError
from radar_desk.ui.ticket_dialog import TicketDialog


FIELD_LABELS = {
    "title": "Título",
    "description": "Descrição",
    "category": "Categoria",
    "priority": "Prioridade",
    "status": "Status",
    "assignee": "Responsável",
}


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
        layout.setContentsMargins(30, 20, 30, 28)
        layout.setSpacing(12)
        layout.addWidget(self._build_toolbar())
        layout.addWidget(self._build_filters())

        content = QHBoxLayout()
        content.setSpacing(12)
        content.addWidget(self._build_list_card(), 3)
        content.addWidget(self._build_detail_card(), 1)
        layout.addLayout(content, 1)

    def _build_toolbar(self) -> QWidget:
        toolbar = QFrame()
        toolbar.setProperty("card", True)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(18, 12, 18, 12)
        toolbar_layout.setSpacing(14)

        copy = QVBoxLayout()
        copy.setSpacing(2)
        title = QLabel("Central de chamados")
        title.setObjectName("sectionTitle")
        caption = QLabel("Busque, filtre e acompanhe cada interação localmente.")
        caption.setProperty("muted", True)
        copy.addWidget(title)
        copy.addWidget(caption)
        toolbar_layout.addLayout(copy, 1)

        self.total_label = QLabel("0 chamados")
        self.total_label.setObjectName("countBadge")
        toolbar_layout.addWidget(self.total_label)

        self.overdue_label = QLabel("0 atrasados")
        self.overdue_label.setObjectName("overdueBadge")
        toolbar_layout.addWidget(self.overdue_label)

        new_button = QPushButton("＋  Novo chamado")
        new_button.setProperty("primary", True)
        new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        new_button.clicked.connect(self._create_ticket)
        toolbar_layout.addWidget(new_button)
        return toolbar

    def _build_filters(self) -> QWidget:
        card = QFrame()
        card.setProperty("card", True)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        first_row = QHBoxLayout()
        first_row.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Buscar protocolo, título, descrição ou responsável..."
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filters_changed)
        first_row.addWidget(self.search_input, 2)

        self.status_filter = self._filter_combo("Todos os status", STATUSES)
        self.priority_filter = self._filter_combo("Prioridades", PRIORITIES)
        self.category_filter = self._filter_combo("Categorias", CATEGORIES)
        first_row.addWidget(self.status_filter)
        first_row.addWidget(self.priority_filter)
        first_row.addWidget(self.category_filter)
        layout.addLayout(first_row)

        second_row = QHBoxLayout()
        second_row.setSpacing(8)
        self.period_check = QCheckBox("Filtrar por abertura")
        self.period_check.toggled.connect(self._toggle_period)
        second_row.addWidget(self.period_check)

        self.start_date = QDateEdit(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        self.start_date.setEnabled(False)
        self.start_date.dateChanged.connect(self._filters_changed)
        second_row.addWidget(self.start_date)

        separator = QLabel("até")
        separator.setProperty("muted", True)
        second_row.addWidget(separator)

        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd/MM/yyyy")
        self.end_date.setEnabled(False)
        self.end_date.dateChanged.connect(self._filters_changed)
        second_row.addWidget(self.end_date)
        second_row.addStretch()

        clear_button = QPushButton("Limpar filtros")
        clear_button.setProperty("secondary", True)
        clear_button.clicked.connect(self.clear_filters)
        second_row.addWidget(clear_button)
        layout.addLayout(second_row)
        return card

    def _filter_combo(self, placeholder: str, values: tuple[str, ...]) -> QComboBox:
        combo = QComboBox()
        combo.addItem(placeholder, "")
        for value in values:
            combo.addItem(value, value)
        combo.currentIndexChanged.connect(self._filters_changed)
        return combo

    def _build_list_card(self) -> QWidget:
        list_card = QFrame()
        list_card.setProperty("card", True)
        list_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(1, 1, 1, 1)

        self.list_stack = QStackedWidget()
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            (
                "Protocolo",
                "Título",
                "Categoria",
                "Prioridade",
                "Status",
                "Responsável",
                "SLA",
                "Atualizado",
            )
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(44)
        header = self.table.horizontalHeader()
        for column in (0, 2, 3, 4, 5, 6, 7):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.itemSelectionChanged.connect(self._show_selection)
        self.table.itemDoubleClicked.connect(lambda _item: self._edit_selected())
        self.list_stack.addWidget(self.table)

        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        empty_layout.setContentsMargins(30, 50, 30, 50)
        empty_layout.addStretch()
        self.empty_icon = QLabel("◎")
        self.empty_icon.setObjectName("emptyIcon")
        self.empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_title = QLabel("Nenhum chamado cadastrado")
        self.empty_title.setObjectName("emptyTitle")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_text = QLabel("Crie o primeiro chamado para começar a usar o Radar Desk.")
        self.empty_text.setProperty("muted", True)
        self.empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_text.setWordWrap(True)
        empty_layout.addWidget(self.empty_icon)
        empty_layout.addWidget(self.empty_title)
        empty_layout.addWidget(self.empty_text)
        empty_layout.addStretch()
        self.list_stack.addWidget(empty)
        list_layout.addWidget(self.list_stack)
        return list_card

    def _build_detail_card(self) -> QWidget:
        detail = QFrame()
        detail.setProperty("card", True)
        detail.setMinimumWidth(320)
        detail.setMaximumWidth(410)
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(14, 16, 14, 14)
        detail_layout.setSpacing(10)
        detail_heading = QLabel("Atendimento")
        detail_heading.setObjectName("sectionTitle")
        detail_layout.addWidget(detail_heading)

        self.detail_tabs = QTabWidget()
        self.detail_tabs.addTab(self._build_summary_tab(), "Resumo")
        self.detail_tabs.addTab(self._build_history_tab(), "Histórico")
        self.detail_tabs.addTab(self._build_comments_tab(), "Comentários")
        detail_layout.addWidget(self.detail_tabs, 1)

        self.reopen_button = QPushButton("↻  Reabrir chamado")
        self.reopen_button.setProperty("secondary", True)
        self.reopen_button.clicked.connect(self._reopen_selected)
        self.reopen_button.hide()
        detail_layout.addWidget(self.reopen_button)

        self.close_button = QPushButton("✓  Confirmar e encerrar")
        self.close_button.setProperty("primary", True)
        self.close_button.clicked.connect(self._close_selected)
        self.close_button.hide()
        detail_layout.addWidget(self.close_button)

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
        return detail

    def _build_summary_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("detailScroll")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 14, 8, 8)
        layout.setSpacing(9)
        self.detail_protocol = QLabel("Selecione um chamado")
        self.detail_protocol.setObjectName("detailProtocol")
        self.detail_title = QLabel("—")
        self.detail_title.setObjectName("detailTitle")
        self.detail_title.setWordWrap(True)
        self.detail_meta = QLabel()
        self.detail_meta.setProperty("muted", True)
        self.detail_meta.setWordWrap(True)
        self.detail_assignee = QLabel()
        self.detail_assignee.setObjectName("assigneeLabel")
        self.detail_assignee.setWordWrap(True)
        self.detail_sla = QLabel()
        self.detail_sla.setObjectName("slaLabel")
        self.detail_sla.setWordWrap(True)
        self.detail_description = QLabel(
            "Os dados completos do chamado selecionado aparecerão aqui."
        )
        self.detail_description.setObjectName("detailDescription")
        self.detail_description.setWordWrap(True)
        self.detail_dates = QLabel()
        self.detail_dates.setProperty("muted", True)
        self.detail_dates.setWordWrap(True)
        layout.addWidget(self.detail_protocol)
        layout.addWidget(self.detail_title)
        layout.addWidget(self.detail_meta)
        layout.addWidget(self.detail_assignee)
        layout.addWidget(self.detail_sla)
        layout.addWidget(self.detail_description)
        layout.addStretch()
        layout.addWidget(self.detail_dates)
        scroll.setWidget(page)
        return scroll

    def _build_history_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 9, 5, 5)
        self.history_list = QListWidget()
        self.history_list.setObjectName("interactionList")
        self.history_list.setWordWrap(True)
        self.history_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.history_list)
        return page

    def _build_comments_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 9, 5, 5)
        layout.setSpacing(7)
        self.comments_list = QListWidget()
        self.comments_list.setObjectName("interactionList")
        self.comments_list.setWordWrap(True)
        self.comments_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        layout.addWidget(self.comments_list, 1)

        self.comment_author = QLineEdit()
        self.comment_author.setPlaceholderText("Autor (opcional)")
        self.comment_author.setMaxLength(100)
        layout.addWidget(self.comment_author)
        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("Registrar comentário ou interação...")
        self.comment_input.setMaximumHeight(76)
        layout.addWidget(self.comment_input)
        self.comment_button = QPushButton("Adicionar comentário")
        self.comment_button.setProperty("primary", True)
        self.comment_button.clicked.connect(self._add_comment)
        layout.addWidget(self.comment_button)
        return page

    def current_filter(self) -> TicketFilter:
        use_period = self.period_check.isChecked()
        return TicketFilter(
            search=self.search_input.text(),
            status=str(self.status_filter.currentData() or ""),
            priority=str(self.priority_filter.currentData() or ""),
            category=str(self.category_filter.currentData() or ""),
            start_date=(self.start_date.date().toString("yyyy-MM-dd") if use_period else ""),
            end_date=(self.end_date.date().toString("yyyy-MM-dd") if use_period else ""),
        )

    def refresh(self, select_id: int | None = None) -> None:
        try:
            tickets = self.service.search(self.current_filter())
        except TicketValidationError as error:
            QMessageBox.warning(self, "Filtro inválido", str(error))
            return
        self.tickets = {ticket.id: ticket for ticket in tickets}
        self.table.setRowCount(len(tickets))
        for row, ticket in enumerate(tickets):
            sla = self.service.sla_for(ticket)
            values = (
                ticket.protocol,
                ticket.title,
                ticket.category,
                ticket.priority,
                ticket.status,
                ticket.assignee or "Não atribuído",
                sla.label,
                Ticket.format_datetime(ticket.updated_at),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, ticket.id)
                if column == 3:
                    self._color_priority(item, ticket.priority)
                if column == 4:
                    self._color_status(item, ticket.status)
                if sla.is_overdue:
                    item.setBackground(QColor("#fff1f2"))
                    item.setForeground(QColor("#be123c"))
                    item.setToolTip(
                        f"SLA vencido em {Ticket.format_datetime(sla.due_at.isoformat())}"
                    )
                elif sla.is_near_due and column == 6:
                    item.setBackground(QColor("#fef3c7"))
                    item.setForeground(QColor("#a16207"))
                self.table.setItem(row, column, item)

        total = self.service.count_all()
        overdue = self.service.count_overdue()
        self.overdue_label.setText(f"{overdue} atrasado" if overdue == 1 else f"{overdue} atrasados")
        if self._has_filters():
            self.total_label.setText(f"{len(tickets)} de {total}")
        else:
            self.total_label.setText(
                "1 chamado" if len(tickets) == 1 else f"{len(tickets)} chamados"
            )
        self.list_stack.setCurrentIndex(0 if tickets else 1)
        if not tickets:
            filtered = self._has_filters()
            self.empty_title.setText(
                "Nenhum resultado encontrado" if filtered else "Nenhum chamado cadastrado"
            )
            self.empty_text.setText(
                "Ajuste ou limpe os filtros para ampliar a busca."
                if filtered
                else "Crie o primeiro chamado para começar a usar o Radar Desk."
            )
            self._clear_details()
        elif select_id is not None:
            self.select_ticket(select_id)
            if not self.selected_ticket():
                self.table.selectRow(0)
        else:
            self.table.selectRow(0)

    def clear_filters(self) -> None:
        self.search_input.clear()
        self.status_filter.setCurrentIndex(0)
        self.priority_filter.setCurrentIndex(0)
        self.category_filter.setCurrentIndex(0)
        self.period_check.setChecked(False)
        self.refresh()

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
        self.detail_meta.setText(f"{ticket.category}  •  {ticket.priority}  •  {ticket.status}")
        self.detail_assignee.setText(f"Responsável: {ticket.assignee or 'Não atribuído'}")
        sla = self.service.sla_for(ticket)
        self.detail_sla.setText(
            f"SLA: {sla.label} · prazo {Ticket.format_datetime(sla.due_at.isoformat())}"
        )
        self.detail_sla.setProperty("slaState", sla.state)
        self.detail_sla.style().unpolish(self.detail_sla)
        self.detail_sla.style().polish(self.detail_sla)
        self.detail_description.setText(ticket.description)
        self.detail_dates.setText(
            f"Aberto em {Ticket.format_datetime(ticket.created_at)}\n"
            f"Atualizado em {Ticket.format_datetime(ticket.updated_at)}"
        )
        self.edit_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.reopen_button.setVisible(ticket.status in ("Resolvido", "Encerrado"))
        self.close_button.setVisible(ticket.status == "Resolvido")
        self.comment_author.setEnabled(True)
        self.comment_input.setEnabled(True)
        self.comment_button.setEnabled(True)
        self._load_interactions(ticket.id)

    def _load_interactions(self, ticket_id: int) -> None:
        self.history_list.clear()
        for history in self.service.get_history(ticket_id):
            text = history.action
            if history.field_name in FIELD_LABELS:
                label = FIELD_LABELS[history.field_name]
                old_value = self._shorten(history.old_value or "—")
                new_value = self._shorten(history.new_value or "—")
                text = f"{label}: {old_value} → {new_value}"
            item = QListWidgetItem(
                f"{text}\n{Ticket.format_datetime(history.created_at)}"
            )
            item.setSizeHint(QSize(0, 52))
            self.history_list.addItem(item)
        if self.history_list.count() == 0:
            self.history_list.addItem("Nenhuma alteração registrada.")

        self.comments_list.clear()
        for comment in self.service.get_comments(ticket_id):
            item = QListWidgetItem(
                f"{comment.author}  •  {Ticket.format_datetime(comment.created_at)}\n"
                f"{comment.content}"
            )
            item.setSizeHint(QSize(0, 68))
            self.comments_list.addItem(item)
        if self.comments_list.count() == 0:
            self.comments_list.addItem("Nenhum comentário registrado.")

    def _clear_details(self) -> None:
        self.table.clearSelection()
        self.detail_protocol.setText("Selecione um chamado")
        self.detail_title.setText("—")
        self.detail_meta.clear()
        self.detail_assignee.clear()
        self.detail_sla.clear()
        self.detail_description.setText(
            "Os dados completos do chamado selecionado aparecerão aqui."
        )
        self.detail_dates.clear()
        self.history_list.clear()
        self.comments_list.clear()
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.reopen_button.hide()
        self.close_button.hide()
        self.comment_author.setEnabled(False)
        self.comment_input.setEnabled(False)
        self.comment_button.setEnabled(False)

    def _create_ticket(self) -> None:
        dialog = TicketDialog(parent=self, category_suggester=self.service.suggest_category)
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
        dialog = TicketDialog(ticket, self, category_suggester=self.service.suggest_category)
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

    def _reopen_selected(self) -> None:
        ticket = self.selected_ticket()
        if not ticket:
            return
        answer = QMessageBox.question(
            self,
            "Reabrir chamado",
            f"Reabrir o chamado {ticket.protocol} com status Aberto?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        reopened = self.service.reopen(ticket.id)
        self.refresh(reopened.id)
        self.tickets_changed.emit()

    def _close_selected(self) -> None:
        ticket = self.selected_ticket()
        if not ticket:
            return
        answer = QMessageBox.question(
            self,
            "Confirmar encerramento",
            f"O chamado {ticket.protocol} está resolvido. Deseja confirmar a solução "
            "e encerrá-lo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            closed = self.service.close_resolved(ticket.id)
        except TicketValidationError as error:
            QMessageBox.warning(self, "Não foi possível encerrar", str(error))
            return
        self.refresh(closed.id)
        self.tickets_changed.emit()

    def _add_comment(self) -> None:
        ticket = self.selected_ticket()
        if not ticket:
            return
        try:
            self.service.add_comment(
                ticket.id,
                self.comment_input.toPlainText(),
                self.comment_author.text(),
            )
        except TicketValidationError as error:
            QMessageBox.warning(self, "Comentário inválido", str(error))
            return
        self.comment_input.clear()
        self.refresh(ticket.id)
        self.detail_tabs.setCurrentIndex(2)

    def _toggle_period(self, enabled: bool) -> None:
        self.start_date.setEnabled(enabled)
        self.end_date.setEnabled(enabled)
        self._filters_changed()

    def _filters_changed(self, *_args) -> None:
        if hasattr(self, "table"):
            self.refresh()

    def _has_filters(self) -> bool:
        filters = self.current_filter()
        return any(
            (
                filters.search.strip(),
                filters.status,
                filters.priority,
                filters.category,
                filters.start_date,
                filters.end_date,
            )
        )

    @staticmethod
    def _shorten(value: str, limit: int = 80) -> str:
        single_line = " ".join(value.split())
        return single_line if len(single_line) <= limit else single_line[: limit - 1] + "…"

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
            "Encerrado": ("#d1d5db", "#374151"),
        }
        background, foreground = colors.get(status, ("#e2e8f0", "#334155"))
        item.setBackground(QColor(background))
        item.setForeground(QColor(foreground))
