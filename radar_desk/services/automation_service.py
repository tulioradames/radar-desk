"""Regras de SLA, categorização e alertas operacionais."""

from __future__ import annotations

import unicodedata
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from radar_desk.models.ticket import Ticket


SLA_HOURS = {
    "Crítica": 4,
    "Alta": 8,
    "Média": 24,
    "Baixa": 48,
}

SLA_WARNING_HOURS = {
    "Crítica": 1,
    "Alta": 2,
    "Média": 4,
    "Baixa": 8,
}

CATEGORY_KEYWORDS = {
    "Rede e internet": (
        "internet", "rede", "wifi", "wi-fi", "vpn", "conexao", "conectar",
        "ping", "dns", "ip", "roteador",
    ),
    "Acesso e permissões": (
        "acesso", "login", "senha", "permissao", "bloqueado", "usuario",
        "credencial", "autenticacao",
    ),
    "Impressão": (
        "impressora", "impressao", "imprimir", "scanner", "toner", "papel",
    ),
    "Hardware": (
        "computador", "notebook", "monitor", "teclado", "mouse", "memoria",
        "disco", "hd", "ssd", "tela", "energia",
    ),
    "Software": (
        "programa", "aplicativo", "sistema", "erro", "atualizacao", "instalar",
        "navegador", "office", "excel", "windows",
    ),
}


@dataclass(frozen=True, slots=True)
class SlaInfo:
    due_at: datetime
    state: str
    remaining: timedelta
    label: str

    @property
    def is_overdue(self) -> bool:
        return self.state == "overdue"

    @property
    def is_near_due(self) -> bool:
        return self.state == "near_due"


@dataclass(frozen=True, slots=True)
class SlaAlert:
    ticket_id: int
    protocol: str
    state: str
    title: str
    message: str


class AutomationService:
    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self.clock = clock or (lambda: datetime.now().astimezone())

    @staticmethod
    def suggest_category(title: str, description: str = "") -> str:
        text = AutomationService._normalize(f"{title} {description}")
        scores = {
            category: sum(
                1 for keyword in keywords if AutomationService._has_keyword(text, keyword)
            )
            for category, keywords in CATEGORY_KEYWORDS.items()
        }
        best_category, best_score = max(scores.items(), key=lambda item: item[1])
        return best_category if best_score else "Outros"

    def sla_for(self, ticket: Ticket, now: datetime | None = None) -> SlaInfo:
        created_at = datetime.fromisoformat(ticket.created_at)
        reference = now or self.clock()
        if created_at.tzinfo is None and reference.tzinfo is not None:
            created_at = created_at.replace(tzinfo=reference.tzinfo)
        elif created_at.tzinfo is not None and reference.tzinfo is None:
            reference = reference.replace(tzinfo=created_at.tzinfo)
        due_at = created_at + timedelta(hours=SLA_HOURS[ticket.priority])
        remaining = due_at - reference
        if ticket.status in ("Resolvido", "Encerrado"):
            state = "completed"
            label = "Concluído"
        elif remaining.total_seconds() < 0:
            state = "overdue"
            label = f"Atrasado {self._duration_label(-remaining)}"
        elif remaining <= timedelta(hours=SLA_WARNING_HOURS[ticket.priority]):
            state = "near_due"
            label = f"Vence em {self._duration_label(remaining)}"
        else:
            state = "on_time"
            label = f"Vence em {self._duration_label(remaining)}"
        return SlaInfo(due_at=due_at, state=state, remaining=remaining, label=label)

    def alerts(self, tickets: Iterable[Ticket]) -> list[SlaAlert]:
        alerts: list[SlaAlert] = []
        for ticket in tickets:
            sla = self.sla_for(ticket)
            if sla.is_overdue:
                alerts.append(
                    SlaAlert(
                        ticket.id,
                        ticket.protocol,
                        sla.state,
                        f"SLA atrasado · {ticket.protocol}",
                        f"{ticket.title} está {sla.label.lower()}.",
                    )
                )
            elif sla.is_near_due:
                alerts.append(
                    SlaAlert(
                        ticket.id,
                        ticket.protocol,
                        sla.state,
                        f"SLA próximo · {ticket.protocol}",
                        f"{ticket.title}: {sla.label.lower()}.",
                    )
                )
        return alerts

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.casefold())
        return "".join(character for character in normalized if not unicodedata.combining(character))

    @staticmethod
    def _has_keyword(text: str, keyword: str) -> bool:
        if len(keyword) <= 3:
            return bool(re.search(rf"\b{re.escape(keyword)}\b", text))
        return keyword in text

    @staticmethod
    def _duration_label(value: timedelta) -> str:
        minutes = max(0, int(value.total_seconds() // 60))
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        if days:
            return f"{days}d {hours}h"
        if hours:
            return f"{hours}h {minutes}min"
        return f"{minutes}min"
