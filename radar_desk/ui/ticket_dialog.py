"""Formulário modal para criação e edição de chamados."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from radar_desk.models.ticket import CATEGORIES, PRIORITIES, STATUSES, Ticket, TicketInput


class TicketDialog(QDialog):
    def __init__(self, ticket: Ticket | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ticket = ticket
        self.setModal(True)
        self.setMinimumWidth(590)
        self.setWindowTitle("Editar chamado" if ticket else "Novo chamado")
        self._build_ui()
        if ticket:
            self._fill(ticket)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        heading = QLabel("Editar chamado" if self.ticket else "Criar novo chamado")
        heading.setObjectName("dialogTitle")
        layout.addWidget(heading)

        subtitle = QLabel(
            f"Protocolo {self.ticket.protocol}" if self.ticket
            else "O protocolo será gerado automaticamente ao salvar."
        )
        subtitle.setProperty("muted", True)
        layout.addWidget(subtitle)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("divider")
        layout.addWidget(divider)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(13)

        self.title_input = QLineEdit()
        self.title_input.setMaxLength(150)
        self.title_input.setPlaceholderText("Ex.: Computador não conecta à rede")
        self.title_input.setClearButtonEnabled(True)
        form.addRow("Título *", self.title_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText(
            "Descreva o problema, quando começou e o impacto percebido."
        )
        self.description_input.setMinimumHeight(145)
        form.addRow("Descrição *", self.description_input)

        self.category_input = QComboBox()
        self.category_input.addItems(CATEGORIES)
        form.addRow("Categoria *", self.category_input)

        self.priority_input = QComboBox()
        self.priority_input.addItems(PRIORITIES)
        self.priority_input.setCurrentText("Média")
        form.addRow("Prioridade *", self.priority_input)

        self.status_input = QComboBox()
        self.status_input.addItems(STATUSES)
        form.addRow("Status *", self.status_input)

        self.assignee_input = QLineEdit()
        self.assignee_input.setMaxLength(100)
        self.assignee_input.setPlaceholderText("Ex.: Equipe de suporte ou nome do atendente")
        self.assignee_input.setClearButtonEnabled(True)
        form.addRow("Responsável", self.assignee_input)
        layout.addLayout(form)

        self.error_label = QLabel()
        self.error_label.setObjectName("formError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        save_button.setText("Salvar chamado")
        save_button.setProperty("primary", True)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("Cancelar")
        cancel_button.setProperty("secondary", True)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _fill(self, ticket: Ticket) -> None:
        self.title_input.setText(ticket.title)
        self.description_input.setPlainText(ticket.description)
        self.category_input.setCurrentText(ticket.category)
        self.priority_input.setCurrentText(ticket.priority)
        self.status_input.setCurrentText(ticket.status)
        self.assignee_input.setText(ticket.assignee)

    def _validate_and_accept(self) -> None:
        title = self.title_input.text().strip()
        description = self.description_input.toPlainText().strip()
        if len(title) < 3:
            self.show_error("Informe um título com pelo menos 3 caracteres.")
            self.title_input.setFocus()
            return
        if len(description) < 5:
            self.show_error("Descreva o problema com pelo menos 5 caracteres.")
            self.description_input.setFocus()
            return
        self.accept()

    def show_error(self, message: str) -> None:
        self.error_label.setText(message)
        self.error_label.show()

    def value(self) -> TicketInput:
        return TicketInput(
            title=self.title_input.text(),
            description=self.description_input.toPlainText(),
            category=self.category_input.currentText(),
            priority=self.priority_input.currentText(),
            status=self.status_input.currentText(),
            assignee=self.assignee_input.text(),
        )
