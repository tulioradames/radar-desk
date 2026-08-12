"""Regras de negócio para gestão operacional de chamados."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from radar_desk.data.ticket_repository import TicketRepository
from radar_desk.services.automation_service import AutomationService, SlaInfo
from radar_desk.models.ticket import (
    CATEGORIES,
    PRIORITIES,
    STATUSES,
    Ticket,
    TicketComment,
    TicketFilter,
    TicketHistory,
    TicketInput,
)


class TicketValidationError(ValueError):
    pass


class TicketService:
    def __init__(
        self,
        repository: TicketRepository,
        clock: Callable[[], datetime] | None = None,
        automation: AutomationService | None = None,
    ) -> None:
        self.repository = repository
        self.clock = clock or (lambda: datetime.now().astimezone())
        self.automation = automation or AutomationService(self.clock)

    def create(self, data: TicketInput) -> Ticket:
        normalized = self._validate(data)
        suggested = self.suggest_category(normalized.title, normalized.description)
        if normalized.category == "Outros" and suggested != "Outros":
            normalized = TicketInput(
                title=normalized.title,
                description=normalized.description,
                category=suggested,
                priority=normalized.priority,
                status=normalized.status,
                assignee=normalized.assignee,
            )
        return self.repository.create(normalized, self.clock())

    def update(self, ticket_id: int, data: TicketInput) -> Ticket:
        normalized = self._validate(data)
        return self.repository.update(ticket_id, normalized, self.clock())

    def delete(self, ticket_id: int) -> None:
        self.repository.delete(ticket_id)

    def get(self, ticket_id: int) -> Ticket:
        return self.repository.get(ticket_id)

    def list_all(self) -> list[Ticket]:
        return self.repository.list_all()

    def search(self, filters: TicketFilter) -> list[Ticket]:
        if filters.start_date and filters.end_date and filters.start_date > filters.end_date:
            raise TicketValidationError("A data inicial não pode ser posterior à data final.")
        return self.repository.list_filtered(filters)

    def reopen(self, ticket_id: int) -> Ticket:
        ticket = self.repository.get(ticket_id)
        if ticket.status not in ("Resolvido", "Encerrado"):
            raise TicketValidationError("Somente chamados resolvidos ou encerrados podem ser reabertos.")
        return self.repository.reopen(ticket_id, self.clock())

    def close_resolved(self, ticket_id: int) -> Ticket:
        ticket = self.repository.get(ticket_id)
        if ticket.status != "Resolvido":
            raise TicketValidationError("Somente chamados resolvidos podem ser encerrados.")
        return self.repository.close_resolved(ticket_id, self.clock())

    def suggest_category(self, title: str, description: str = "") -> str:
        return self.automation.suggest_category(title, description)

    def sla_for(self, ticket: Ticket) -> SlaInfo:
        return self.automation.sla_for(ticket)

    def count_overdue(self) -> int:
        return sum(self.automation.sla_for(ticket).is_overdue for ticket in self.list_all())

    def add_comment(
        self,
        ticket_id: int,
        content: str,
        author: str = "Usuário local",
    ) -> TicketComment:
        normalized_content = content.strip()
        normalized_author = author.strip() or "Usuário local"
        if len(normalized_content) < 2:
            raise TicketValidationError("Escreva um comentário antes de adicionar.")
        if len(normalized_content) > 2000:
            raise TicketValidationError("O comentário deve ter no máximo 2.000 caracteres.")
        if len(normalized_author) > 100:
            raise TicketValidationError("O nome do autor deve ter no máximo 100 caracteres.")
        return self.repository.add_comment(
            ticket_id,
            normalized_author,
            normalized_content,
            self.clock(),
        )

    def get_comments(self, ticket_id: int) -> list[TicketComment]:
        return self.repository.get_comments(ticket_id)

    def get_history(self, ticket_id: int) -> list[TicketHistory]:
        return self.repository.get_history(ticket_id)

    def count_all(self) -> int:
        return self.repository.count_all()

    def count_active(self) -> int:
        return self.repository.count_active()

    @staticmethod
    def _validate(data: TicketInput) -> TicketInput:
        title = data.title.strip()
        description = data.description.strip()
        assignee = data.assignee.strip()
        if len(title) < 3:
            raise TicketValidationError("O título deve ter pelo menos 3 caracteres.")
        if len(title) > 150:
            raise TicketValidationError("O título deve ter no máximo 150 caracteres.")
        if len(description) < 5:
            raise TicketValidationError("A descrição deve ter pelo menos 5 caracteres.")
        if data.category not in CATEGORIES:
            raise TicketValidationError("Selecione uma categoria válida.")
        if data.priority not in PRIORITIES:
            raise TicketValidationError("Selecione uma prioridade válida.")
        if data.status not in STATUSES:
            raise TicketValidationError("Selecione um status válido.")
        if len(assignee) > 100:
            raise TicketValidationError("O responsável deve ter no máximo 100 caracteres.")
        return TicketInput(
            title=title,
            description=description,
            category=data.category,
            priority=data.priority,
            status=data.status,
            assignee=assignee,
        )
