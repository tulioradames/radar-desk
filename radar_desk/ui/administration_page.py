"""Administração local de usuários, auditoria e sincronização."""

from __future__ import annotations

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QTabWidget, QVBoxLayout, QWidget,
)

from radar_desk.models.ticket import Ticket
from radar_desk.models.user import ROLES, User
from radar_desk.services.auth_service import AuthError, AuthService
from radar_desk.services.sync_service import SyncConfigurationError, SyncService


class SyncWorker(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, service: SyncService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service

    def run(self) -> None:
        try:
            self.completed.emit(self.service.synchronize())
        except Exception as error:
            self.failed.emit(str(error))


class UserDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Novo usuário local")
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        title = QLabel("Criar usuário local")
        title.setObjectName("dialogTitle")
        layout.addWidget(title)
        form = QFormLayout()
        self.name_input = QLineEdit()
        self.username_input = QLineEdit()
        self.role_input = QComboBox()
        self.role_input.addItems(ROLES)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Nome", self.name_input)
        form.addRow("Usuário", self.username_input)
        form.addRow("Perfil", self.role_input)
        form.addRow("Senha inicial", self.password_input)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Criar usuário")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class AdministrationPage(QWidget):
    def __init__(
        self, user: User, auth_service: AuthService, sync_service: SyncService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.user = user
        self.auth_service = auth_service
        self.sync_service = sync_service
        self.worker: SyncWorker | None = None
        self._build_ui()
        self.refresh()
        self.auto_timer = QTimer(self)
        self.auto_timer.setInterval(60_000)
        self.auto_timer.timeout.connect(self._auto_sync)
        self.auto_timer.start()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 22, 30, 28)
        layout.setSpacing(12)
        account = QFrame()
        account.setProperty("card", True)
        row = QHBoxLayout(account)
        row.setContentsMargins(18, 14, 18, 14)
        copy = QVBoxLayout()
        title = QLabel(f"{self.user.display_name} · {self.user.role}")
        title.setObjectName("sectionTitle")
        subtitle = QLabel(f"Sessão local: @{self.user.username}")
        subtitle.setProperty("muted", True)
        copy.addWidget(title)
        copy.addWidget(subtitle)
        row.addLayout(copy, 1)
        self.pending_label = QLabel("0 pendentes")
        self.pending_label.setObjectName("countBadge")
        row.addWidget(self.pending_label)
        self.sync_button = QPushButton("Sincronizar agora")
        self.sync_button.setProperty("primary", True)
        self.sync_button.clicked.connect(self._sync)
        row.addWidget(self.sync_button)
        layout.addWidget(account)
        self.status_label = QLabel()
        self.status_label.setObjectName("privacyNotice")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        tabs = QTabWidget()
        tabs.addTab(self._build_queue_tab(), "Fila offline")
        tabs.addTab(self._build_audit_tab(), "Auditoria")
        if self.user.can_administer:
            tabs.addTab(self._build_users_tab(), "Usuários")
        layout.addWidget(tabs, 1)

    def _build_queue_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.queue_list = QListWidget()
        self.queue_list.setObjectName("interactionList")
        layout.addWidget(self.queue_list)
        return page

    def _build_audit_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.audit_list = QListWidget()
        self.audit_list.setObjectName("interactionList")
        layout.addWidget(self.audit_list)
        return page

    def _build_users_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        buttons = QHBoxLayout()
        buttons.addStretch()
        add_button = QPushButton("＋ Novo usuário")
        add_button.setProperty("primary", True)
        add_button.clicked.connect(self._create_user)
        buttons.addWidget(add_button)
        layout.addLayout(buttons)
        self.users_list = QListWidget()
        self.users_list.setObjectName("interactionList")
        layout.addWidget(self.users_list)
        return page

    def refresh(self) -> None:
        pending = self.sync_service.repository.pending()
        self.pending_label.setText(f"{len(pending)} pendente(s)")
        self.queue_list.clear()
        for event in pending:
            self.queue_list.addItem(
                f"{event.entity_type} · {event.entity_id} · {event.operation}\n"
                f"Versão local {event.local_version} · tentativas {event.attempts}"
                + (f" · {event.last_error}" if event.last_error else "")
            )
        if not pending:
            self.queue_list.addItem("Fila vazia. Todas as alterações locais estão processadas.")
        configured = self.sync_service.configured
        self.status_label.setText(
            "Supabase configurado. A fila será reenviada automaticamente quando a conexão retornar."
            if configured else
            "Modo offline ativo. Para sincronizar, configure SUPABASE_URL, SUPABASE_ANON_KEY "
            "e SUPABASE_ACCESS_TOKEN. A fila local está preservada."
        )
        self.sync_button.setEnabled(bool(pending) and configured and self.worker is None)
        self.audit_list.clear()
        for entry in self.auth_service.list_audit():
            self.audit_list.addItem(
                f"{entry.action} · @{entry.username}\n"
                f"{entry.entity_type} {entry.entity_id} · {Ticket.format_datetime(entry.created_at)}"
            )
        if hasattr(self, "users_list"):
            self.users_list.clear()
            for item in self.auth_service.list_users():
                state = "Ativo" if item.active else "Desativado"
                row = QListWidgetItem(f"{item.display_name} · @{item.username}\n{item.role} · {state}")
                self.users_list.addItem(row)

    def _sync(self) -> None:
        if self.worker:
            return
        self.sync_button.setEnabled(False)
        self.status_label.setText("Sincronizando alterações pendentes...")
        self.worker = SyncWorker(self.sync_service, self)
        self.worker.completed.connect(self._sync_completed)
        self.worker.failed.connect(self._sync_failed)
        self.worker.finished.connect(self._worker_finished)
        self.worker.start()

    def _auto_sync(self) -> None:
        if self.sync_service.configured and self.sync_service.pending_count() and not self.worker:
            self._sync()

    def _sync_completed(self, result) -> None:
        self.status_label.setText(
            f"Sincronização concluída: {result.succeeded} sucesso(s), "
            f"{result.failed} falha(s) e {result.conflicts} conflito(s) resolvido(s)."
        )

    def _sync_failed(self, message: str) -> None:
        self.status_label.setText(message)

    def _worker_finished(self) -> None:
        worker = self.worker
        self.worker = None
        if worker:
            worker.deleteLater()
        self.refresh()

    def _create_user(self) -> None:
        dialog = UserDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            created = self.auth_service.create_user(
                dialog.username_input.text(), dialog.name_input.text(),
                dialog.role_input.currentText(), dialog.password_input.text()
            )
            self.auth_service.audit(self.user, "Usuário criado", "user", str(created.id), created.role)
        except AuthError as error:
            QMessageBox.warning(self, "Usuário inválido", str(error))
            return
        self.refresh()
