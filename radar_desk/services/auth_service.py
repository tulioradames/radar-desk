"""Autenticação local segura e auditoria de sessão."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from collections.abc import Callable
from datetime import datetime

from radar_desk.data.auth_repository import AuthRepository
from radar_desk.models.user import ROLES, AuditEntry, User


class AuthError(ValueError):
    pass


class AuthService:
    ITERATIONS = 310_000

    def __init__(
        self,
        repository: AuthRepository,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.clock = clock or (lambda: datetime.now().astimezone())

    def needs_setup(self) -> bool:
        return self.repository.count_users() == 0

    def create_user(
        self, username: str, display_name: str, role: str, password: str
    ) -> User:
        username = username.strip().lower()
        display_name = display_name.strip()
        if not re.fullmatch(r"[a-z0-9._-]{3,40}", username):
            raise AuthError("O usuário deve ter de 3 a 40 caracteres: letras, números, ponto, hífen ou sublinhado.")
        if len(display_name) < 2 or len(display_name) > 100:
            raise AuthError("Informe um nome com 2 a 100 caracteres.")
        if role not in ROLES:
            raise AuthError("Selecione um perfil válido.")
        self._validate_password(password)
        salt = os.urandom(16)
        password_hash = self._hash(password, salt)
        try:
            return self.repository.create_user(
                username, display_name, role, password_hash.hex(), salt.hex(), self.clock()
            )
        except Exception as error:
            if "UNIQUE constraint" in str(error):
                raise AuthError("Este nome de usuário já existe.") from error
            raise

    def setup_admin(self, username: str, display_name: str, password: str) -> User:
        if not self.needs_setup():
            raise AuthError("A configuração inicial já foi concluída.")
        user = self.create_user(username, display_name, "Administrador", password)
        self.audit(user, "Configuração inicial", "user", str(user.id), user.role)
        return user

    def authenticate(self, username: str, password: str) -> User:
        row = self.repository.credentials_for(username.strip())
        if not row or not bool(row["active"]):
            raise AuthError("Usuário ou senha inválidos.")
        salt = bytes.fromhex(str(row["password_salt"]))
        candidate = self._hash(password, salt)
        expected = bytes.fromhex(str(row["password_hash"]))
        if not hmac.compare_digest(candidate, expected):
            raise AuthError("Usuário ou senha inválidos.")
        user = AuthRepository._user_from_row(row)
        self.audit(user, "Login local", "session", str(user.id), user.role)
        return user

    def list_users(self) -> list[User]:
        return self.repository.list_users()

    def set_active(self, actor: User, user_id: int, active: bool) -> None:
        if not actor.can_administer:
            raise AuthError("Somente administradores podem alterar usuários.")
        if actor.id == user_id and not active:
            raise AuthError("Você não pode desativar o próprio usuário.")
        self.repository.set_active(user_id, active, self.clock())
        self.audit(actor, "Usuário ativado" if active else "Usuário desativado", "user", str(user_id), "")

    def audit(
        self, user: User | None, action: str, entity_type: str,
        entity_id: str = "", details: str = ""
    ) -> None:
        self.repository.add_audit(user, action, entity_type, entity_id, details, self.clock())

    def list_audit(self, limit: int = 200) -> list[AuditEntry]:
        return self.repository.list_audit(limit)

    @classmethod
    def _hash(cls, password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, cls.ITERATIONS)

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 8 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            raise AuthError("A senha deve ter ao menos 8 caracteres, uma letra e um número.")
