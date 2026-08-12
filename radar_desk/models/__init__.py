"""Entidades de domínio do Radar Desk."""

from radar_desk.models.attachment import TicketAttachment
from radar_desk.models.ticket import (
    Ticket,
    TicketComment,
    TicketFilter,
    TicketHistory,
    TicketInput,
)

__all__ = [
    "Ticket",
    "TicketAttachment",
    "TicketComment",
    "TicketFilter",
    "TicketHistory",
    "TicketInput",
]
