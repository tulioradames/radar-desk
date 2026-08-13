"""Entidades e opções permitidas para chamados."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


CATEGORIES = (
    "Hardware",
    "Software",
    "Rede e internet",
    "Acesso e permissões",
    "Impressão",
    "Outros",
)

PRIORITIES = ("Baixa", "Média", "Alta", "Crítica")
STATUSES = ("Aberto", "Em andamento", "Aguardando", "Resolvido", "Encerrado")


@dataclass(frozen=True, slots=True)
class TicketInput:
    title: str
    description: str
    category: str
    priority: str
    status: str = "Aberto"
    assignee: str = ""


@dataclass(frozen=True, slots=True)
class TicketFilter:
    search: str = ""
    status: str = ""
    priority: str = ""
    category: str = ""
    start_date: str = ""
    end_date: str = ""


@dataclass(frozen=True, slots=True)
class Ticket:
    id: int
    protocol: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    assignee: str
    created_at: str
    updated_at: str

    @staticmethod
    def format_datetime(value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value)
            return parsed.strftime("%d/%m/%Y às %H:%M")
        except ValueError:
            return value


@dataclass(frozen=True, slots=True)
class TicketHistory:
    id: int
    ticket_id: int
    action: str
    field_name: str
    old_value: str
    new_value: str
    created_at: str


@dataclass(frozen=True, slots=True)
class TicketComment:
    id: int
    ticket_id: int
    author: str
    content: str
    created_at: str
