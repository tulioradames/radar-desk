"""Ponto de entrada do Radar Desk."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from radar_desk.core.config import APP_NAME, APP_VERSION, get_app_paths
from radar_desk.core.logging_config import configure_logging
from radar_desk.data.database import Database
from radar_desk.ui.main_window import MainWindow


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("RadarDesk")
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(str(Path(__file__).parent / "resources" / "radar_desk.svg")))

    paths = get_app_paths()
    paths.ensure()
    configure_logging(paths.logs_dir)
    logger = logging.getLogger(__name__)

    try:
        database = Database(paths.database)
        database.initialize()
        window = MainWindow(database, paths.files_dir)
        window.show()
        logger.info("Radar Desk v%s iniciado", APP_VERSION)
        return app.exec()
    except Exception as error:  # proteção da fronteira da aplicação
        logger.exception("Falha ao iniciar o Radar Desk")
        QMessageBox.critical(
            None,
            "Falha ao iniciar",
            f"O Radar Desk não pôde ser iniciado.\n\nDetalhes: {error}",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
