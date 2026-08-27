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
from radar_desk.data.auth_repository import AuthRepository
from radar_desk.data.sync_repository import SyncRepository
from radar_desk.services.auth_service import AuthService
from radar_desk.services.sync_service import SyncService
from radar_desk.ui.login_dialog import LoginDialog
from radar_desk.ui.main_window import MainWindow
from radar_desk.ui.theme import Theme, stylesheet


def run_self_test() -> int:
    """Valida a inicialização do armazenamento sem abrir a interface."""

    paths = get_app_paths()
    paths.ensure()
    configure_logging(paths.logs_dir)
    database = Database(paths.database)
    database.initialize()
    logging.getLogger(__name__).info(
        "Autoteste do Radar Desk v%s concluído", APP_VERSION
    )
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        try:
            return run_self_test()
        except Exception:
            logging.exception("Falha no autoteste do Radar Desk")
            return 1

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
        app.setStyleSheet(stylesheet(Theme.LIGHT))
        auth_repository = AuthRepository(database)
        auth_service = AuthService(auth_repository)
        login = LoginDialog(auth_service)
        if login.exec() != LoginDialog.DialogCode.Accepted or not login.user:
            logger.info("Login cancelado")
            return 0
        sync_service = SyncService(
            database,
            SyncRepository(database),
            auth_repository,
            login.user,
        )
        window = MainWindow(
            database,
            paths.files_dir,
            login.user,
            auth_service,
            sync_service,
        )
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
