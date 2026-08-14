"""Modelos imutáveis usados pelos relatórios operacionais."""

from __future__ import annotations

from dataclasses import dataclass

from radar_desk.models.ticket import Ticket


@dataclass(frozen=True, slots=True)
class ReportFilter:
    start_date: str = ""
    end_date: str = ""


@dataclass(frozen=True, slots=True)
class TicketRating:
    id: int
    ticket_id: int
    rating: int
    comment: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ReportSnapshot:
    generated_at: str
    start_date: str
    end_date: str
    total: int
    active: int
    completed: int
    overdue: int
    average_resolution_hours: float | None
    average_rating: float | None
    rating_count: int
    status_counts: tuple[tuple[str, int], ...]
    category_counts: tuple[tuple[str, int], ...]
    priority_counts: tuple[tuple[str, int], ...]
    volume_by_day: tuple[tuple[str, int], ...]
    overdue_tickets: tuple[Ticket, ...]
    tickets: tuple[Ticket, ...]
