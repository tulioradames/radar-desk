import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings  # noqa: E402
from PySide6.QtGui import QColor, QPixmap  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from radar_desk.data.database import Database  # noqa: E402
from radar_desk.models.diagnostic import DiagnosticSnapshot  # noqa: E402
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
        assert window.pages.count() == 7
        assert len(window.nav_buttons) == 7
        assert window.database.health_check()
        assert window.tickets_page.list_stack.currentIndex() == 1
        assert window.diagnostic_page.ticket_combo.count() == 1
        assert window.attachments_page.ticket_combo.count() == 1
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


def test_diagnostic_page_shows_exact_preview_fields() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        window = MainWindow(database, Path(directory) / "arquivos")
        ticket = window.ticket_service.create(
            TicketInput(
                title="Diagnosticar lentidão",
                description="A estação está lenta desde o início do dia.",
                category="Hardware",
                priority="Alta",
            )
        )
        window.diagnostic_page.refresh_tickets(ticket.id)
        snapshot = DiagnosticSnapshot(
            collected_at="2026-08-10T16:00:00+00:00",
            operating_system="Windows",
            os_version="Windows 11",
            architecture="AMD64",
            computer_name="RADAR-PC",
            user_name="usuario",
            local_ip="192.168.1.25",
            memory_total_bytes=16 * 1024**3,
            memory_used_bytes=8 * 1024**3,
            memory_percent=50.0,
            storage_drive="C:\\",
            storage_total_bytes=500 * 1024**3,
            storage_used_bytes=200 * 1024**3,
            storage_free_bytes=300 * 1024**3,
            storage_percent=40.0,
            connection_status="Conectado",
            ping_target="1.1.1.1",
            ping_success=True,
            ping_latency_ms=12.5,
        )

        window.diagnostic_page._show_snapshot(snapshot)

        assert window.diagnostic_page.data_table.rowCount() == 19
        assert "Nada foi anexado" in window.diagnostic_page.data_subtitle.text()
        assert window.diagnostic_page.capture_button.isEnabled()
        assert window.diagnostic_page.attach_button.isEnabled()
        window.diagnostic_page.screenshot = QPixmap(12, 12)
        window.diagnostic_page.screenshot.fill(QColor("#2dd4bf"))
        screenshot = window.diagnostic_page._screenshot_bytes()
        assert screenshot is not None
        assert screenshot.startswith(b"\x89PNG")
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


def test_attachment_page_previews_and_navigates_images() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory() as directory:
        root = Path(directory)
        database = Database(root / "test.sqlite3")
        database.initialize()
        window = MainWindow(database, root / "arquivos")
        ticket = window.ticket_service.create(
            TicketInput(
                title="Evidências da tela",
                description="Imagens mostram o erro apresentado pelo sistema.",
                category="Software",
                priority="Média",
            )
        )
        sources = root / "fontes"
        sources.mkdir()
        for name, color in (("erro-1.png", "#2dd4bf"), ("erro-2.png", "#60a5fa")):
            pixmap = QPixmap(80, 50)
            pixmap.fill(QColor(color))
            assert pixmap.save(str(sources / name), "PNG")

        attached = window.attachment_service.attach_many(ticket, sources.glob("*.png"))
        page = window.attachments_page
        page.refresh_tickets(ticket.id)
        records = window.attachment_service.list_for_ticket(ticket.id)
        page.viewer.set_attachments(records)
        page.viewer.show_attachment(records[0])

        assert len(attached) == 2
        assert page.files_list.count() == 2
        assert not page.viewer.original_pixmap.isNull()
        page.viewer.change_zoom(1.25)
        assert page.viewer.fit_to_window is False
        page.viewer.rotate_image(90)
        assert page.viewer.rotation == 90
        page.viewer.next_image()
        assert page.viewer.current == records[1]
        window.close()
    app.processEvents()
