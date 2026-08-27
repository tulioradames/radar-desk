"""Login local e configuração segura do primeiro administrador."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
)

from radar_desk.models.user import User
from radar_desk.services.auth_service import AuthError, AuthService
from radar_desk.ui.widgets import RadarLogo


class LoginDialog(QDialog):
    def __init__(self, service: AuthService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.service = service
        self.user: User | None = None
        self.setup_mode = service.needs_setup()
        self.setWindowTitle("Primeiro acesso" if self.setup_mode else "Entrar no Radar Desk")
        self.setModal(True)
        self.setFixedWidth(440)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 32)
        layout.setSpacing(15)
        logo = RadarLogo(72)
        layout.addWidget(logo, 0, Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Configure o administrador" if self.setup_mode else "Bem-vindo ao Radar Desk")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        detail = QLabel(
            "Crie a conta que administrará usuários e sincronização neste computador."
            if self.setup_mode else "Entre com sua conta local. A internet não é necessária."
        )
        detail.setProperty("muted", True)
        detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail.setWordWrap(True)
        layout.addWidget(detail)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("divider")
        layout.addWidget(divider)
        form = QFormLayout()
        form.setVerticalSpacing(12)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex.: Túlio Radames")
        if self.setup_mode:
            form.addRow("Nome", self.name_input)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ex.: tulio")
        form.addRow("Usuário", self.username_input)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Mínimo 8 caracteres, letra e número")
        self.password_input.returnPressed.connect(self._submit)
        form.addRow("Senha", self.password_input)
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self.setup_mode:
            self.confirm_input.returnPressed.connect(self._submit)
            form.addRow("Confirmar", self.confirm_input)
        layout.addLayout(form)
        self.error_label = QLabel()
        self.error_label.setObjectName("formError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        button = QPushButton("Criar administrador" if self.setup_mode else "Entrar")
        button.setProperty("primary", True)
        button.clicked.connect(self._submit)
        layout.addWidget(button)

    def _submit(self) -> None:
        try:
            if self.setup_mode:
                if self.password_input.text() != self.confirm_input.text():
                    raise AuthError("As senhas não coincidem.")
                self.user = self.service.setup_admin(
                    self.username_input.text(), self.name_input.text(), self.password_input.text()
                )
            else:
                self.user = self.service.authenticate(
                    self.username_input.text(), self.password_input.text()
                )
        except AuthError as error:
            self.error_label.setText(str(error))
            self.error_label.show()
            return
        self.accept()
