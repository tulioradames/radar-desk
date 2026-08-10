import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from radar_desk.data.database import Database  # noqa: E402
from radar_desk.models.ticket import TicketInput  # noqa: E402
from radar_desk.ui.main_window import MainWindow  # noqa: E402
from radar_desk.ui.theme import Theme  # noqa: E402


def test_main_window_has_all_base_pages() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        window = MainWindow(database)

        assert window.windowTitle().startswith("Radar Desk")
        assert window.pages.count() == 5
        assert len(window.nav_buttons) == 5
        assert window.database.health_check()
        assert window.tickets_page.list_stack.currentIndex() == 1
        window.close()
    app.processEvents()


def test_ticket_page_updates_after_local_creation() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        window = MainWindow(database)
        ticket = window.ticket_service.create(
            TicketInput(
                title="Falha no monitor",
                description="O monitor principal não exibe imagem.",
                category="Hardware",
                priority="Alta",
                assignee="Equipe de Campo",
            )
        )

        window.tickets_page.refresh(ticket.id)

        assert window.tickets_page.table.rowCount() == 1
        assert window.tickets_page.selected_ticket() == ticket
        assert window.tickets_page.detail_protocol.text() == ticket.protocol
        assert "Equipe de Campo" in window.tickets_page.detail_assignee.text()
        window.close()
    app.processEvents()


def test_ticket_page_general_search_filters_rows() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        window = MainWindow(database)
        window.ticket_service.create(
            TicketInput(
                title="Falha na VPN",
                description="A VPN não estabelece conexão.",
                category="Rede e internet",
                priority="Alta",
                assignee="Equipe Redes",
            )
        )
        window.ticket_service.create(
            TicketInput(
                title="Atualizar navegador",
                description="O navegador está em versão antiga.",
                category="Software",
                priority="Baixa",
            )
        )
        window.tickets_page.refresh()

        window.tickets_page.search_input.setText("Equipe Redes")

        assert window.tickets_page.table.rowCount() == 1
        assert window.tickets_page.selected_ticket().title == "Falha na VPN"
        window.close()
    app.processEvents()


def test_theme_can_be_switched() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        window = MainWindow(database)
        window.settings = QSettings(
            str(Path(directory) / "settings.ini"), QSettings.Format.IniFormat
        )
        initial = window.current_theme

        window._toggle_theme()

        expected = Theme.DARK if initial is Theme.LIGHT else Theme.LIGHT
        assert window.current_theme is expected
        window.close()
    app.processEvents()
