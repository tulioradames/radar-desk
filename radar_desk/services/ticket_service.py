"""Regras de negócio da versão 0.2."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from radar_desk.data.ticket_repository import TicketRepository
from radar_desk.models.ticket import CATEGORIES, PRIORITIES, STATUSES, Ticket, TicketInput


class TicketValidationError(ValueError):
    pass


class TicketService:
    def __init__(
        self,
        repository: TicketRepository,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.repository = repository
        self.clock = clock or (lambda: datetime.now().astimezone())

    def create(self, data: TicketInput) -> Ticket:
        normalized = self._validate(data)
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

    def count_all(self) -> int:
        return self.repository.count_all()

    def count_active(self) -> int:
        return self.repository.count_active()

    @staticmethod
    def _validate(data: TicketInput) -> TicketInput:
        title = data.title.strip()
        description = data.description.strip()
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
        return TicketInput(
            title=title,
            description=description,
            category=data.category,
            priority=data.priority,
            status=data.status,
        )
