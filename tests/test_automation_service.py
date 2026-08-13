from datetime import datetime, timedelta, timezone

from radar_desk.models.ticket import Ticket
from radar_desk.services.automation_service import AutomationService


def ticket_at(
    created_at: datetime,
    *,
    priority: str = "Alta",
    status: str = "Aberto",
    ticket_id: int = 1,
) -> Ticket:
    timestamp = created_at.isoformat(timespec="seconds")
    return Ticket(
        id=ticket_id,
        protocol=f"RD-2026-{ticket_id:04d}",
        title="Falha na VPN",
        description="A conexão não é estabelecida.",
        category="Rede e internet",
        priority=priority,
        status=status,
        assignee="Equipe Redes",
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_sla_deadlines_follow_priority_and_signal_risk() -> None:
    now = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
    service = AutomationService(clock=lambda: now)

    critical = service.sla_for(ticket_at(now - timedelta(hours=3, minutes=30), priority="Crítica"))
    high = service.sla_for(ticket_at(now - timedelta(hours=9), priority="Alta", ticket_id=2))
    completed = service.sla_for(
        ticket_at(now - timedelta(days=3), priority="Baixa", status="Encerrado", ticket_id=3)
    )

    assert critical.state == "near_due"
    assert critical.due_at == now + timedelta(minutes=30)
    assert high.state == "overdue"
    assert "Atrasado" in high.label
    assert completed.state == "completed"


def test_alerts_include_only_near_and_overdue_active_tickets() -> None:
    now = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
    service = AutomationService(clock=lambda: now)
    tickets = [
        ticket_at(now - timedelta(hours=7), ticket_id=1),
        ticket_at(now - timedelta(hours=9), ticket_id=2),
        ticket_at(now, priority="Baixa", ticket_id=3),
        ticket_at(now - timedelta(days=2), status="Resolvido", ticket_id=4),
    ]

    alerts = service.alerts(tickets)

    assert [(alert.ticket_id, alert.state) for alert in alerts] == [
        (1, "near_due"),
        (2, "overdue"),
    ]


def test_category_suggestion_uses_keywords_without_accents() -> None:
    service = AutomationService()

    assert service.suggest_category("Sem conexão na VPN") == "Rede e internet"
    assert service.suggest_category("Usuário bloqueado", "Senha não funciona") == "Acesso e permissões"
    assert service.suggest_category("Trocar toner da impressora") == "Impressão"
    assert service.suggest_category("Solicitação genérica") == "Outros"
