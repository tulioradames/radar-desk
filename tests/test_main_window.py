import os
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from radar_desk.data.database import Database  # noqa: E402
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
        window.close()
    app.processEvents()


def test_theme_can_be_switched() -> None:
    app = QApplication.instance() or QApplication([])
    with TemporaryDirectory() as directory:
        database = Database(Path(directory) / "test.sqlite3")
        database.initialize()
        window = MainWindow(database)
        initial = window.current_theme

        window._toggle_theme()

        expected = Theme.DARK if initial is Theme.LIGHT else Theme.LIGHT
        assert window.current_theme is expected
        window.close()
    app.processEvents()
