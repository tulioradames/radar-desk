"""Carga opcional de dados demonstrativos para apresentações."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from radar_desk.data.database import Database
from radar_desk.data.ticket_repository import TicketRepository
from radar_desk.models.ticket import TicketInput


class DemoDataService:
    SETTING_KEY = "demo_data_loaded"

    def __init__(
        self,
        database: Database,
        repository: TicketRepository,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.database = database
        self.repository = repository
        self.clock = clock or (lambda: datetime.now().astimezone())

    def is_loaded(self) -> bool:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_settings WHERE key = ?", (self.SETTING_KEY,)
            ).fetchone()
        return bool(row and str(row["value"]) == "1")

    def load(self) -> int:
        if self.is_loaded():
            return 0
        now = self.clock()
        samples = (
            (
                -72,
                TicketInput(
                    "Falha crítica no concentrador",
                    "Equipamento principal sem comunicação desde o início do turno.",
                    "Rede e internet",
                    "Crítica",
                    "Aberto",
                    "Equipe N2",
                ),
                None,
            ),
            (
                -48,
                TicketInput(
                    "Sistema comercial indisponível",
                    "Aplicação apresenta erro ao autenticar os atendentes.",
                    "Software",
                    "Alta",
                    "Em andamento",
                    "Equipe Apps",
                ),
                None,
            ),
            (
                -26,
                TicketInput(
                    "Liberação de acesso ao financeiro",
                    "Usuária necessita consultar os relatórios mensais.",
                    "Acesso e permissões",
                    "Média",
                    "Aberto",
                    "Service Desk",
                ),
                ("Resolvido", 4),
            ),
            (
                -18,
                TicketInput(
                    "Impressora da recepção pausada",
                    "Fila de impressão não libera novos documentos.",
                    "Impressão",
                    "Baixa",
                    "Aguardando",
                    "Suporte local",
                ),
                None,
            ),
            (
                -10,
                TicketInput(
                    "Substituição de teclado",
                    "Teclas apresentam falhas durante a digitação.",
                    "Hardware",
                    "Baixa",
                    "Aberto",
                    "Equipe de Campo",
                ),
                ("Encerrado", 2),
            ),
            (
                -3,
                TicketInput(
                    "Atualização do navegador",
                    "Versão instalada não é compatível com o portal interno.",
                    "Software",
                    "Média",
                    "Aberto",
                    "Equipe N1",
                ),
                None,
            ),
        )
        created = 0
        for hours, data, conclusion in samples:
            opened_at = now + timedelta(hours=hours)
            ticket = self.repository.create(data, opened_at)
            created += 1
            if conclusion:
                status, elapsed_hours = conclusion
                updated = TicketInput(
                    data.title,
                    data.description,
                    data.category,
                    data.priority,
                    status,
                    data.assignee,
                )
                self.repository.update(
                    ticket.id, updated, opened_at + timedelta(hours=elapsed_hours)
                )

        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, '1', CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
                """,
                (self.SETTING_KEY,),
            )
        return created
