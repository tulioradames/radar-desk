"""Janela principal do Radar Desk."""

from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from radar_desk.core.config import APP_NAME, APP_VERSION, ORGANIZATION_NAME
from radar_desk.data.database import Database
from radar_desk.data.ticket_repository import TicketRepository
from radar_desk.services.ticket_service import TicketService
from radar_desk.ui.theme import Theme, stylesheet
from radar_desk.ui.tickets_page import TicketsPage
from radar_desk.ui.widgets import RadarLogo, RoadmapItem, StatCard


class MainWindow(QMainWindow):
    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.ticket_service = TicketService(TicketRepository(database))
        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        self.nav_buttons: list[QPushButton] = []
        self.page_metadata: list[tuple[str, str]] = []

        self.setWindowTitle(f"{APP_NAME} — v{APP_VERSION}")
        self.setMinimumSize(1040, 680)
        self.resize(1280, 780)
        self._build_ui()
        self._restore_theme()
        self._select_page(0)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("appRoot")
        self.setCentralWidget(root)

        shell = QVBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)
        shell.addWidget(self._build_topbar())

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._build_header())

        self.pages = QStackedWidget()
        self.pages.setObjectName("pageStack")
        self._add_page(
            "Visão geral",
            "Acompanhe a evolução e o estado local do Radar Desk.",
            self._build_dashboard(),
        )
        self.tickets_page = TicketsPage(self.ticket_service)
        self.tickets_page.tickets_changed.connect(self._refresh_dashboard)
        self._add_page(
            "Chamados",
            "Busque, filtre e registre todo o fluxo de atendimento local.",
            self.tickets_page,
        )
        self._add_page(
            "Diagnóstico",
            "Coleta transparente de informações do computador.",
            self._build_coming_page("0.4", "Diagnóstico automático", "A coleta só será anexada após mostrar e confirmar todos os dados."),
        )
        self._add_page(
            "Relatórios",
            "Indicadores operacionais e exportações.",
            self._build_coming_page("0.8", "Relatórios e indicadores", "Painéis, Excel e PDF serão adicionados nesta etapa."),
        )
        self._add_page(
            "Configurações",
            "Preferências locais do aplicativo.",
            self._build_settings_page(),
        )
        body_layout.addWidget(self.pages, 1)
        shell.addWidget(body, 1)

    def _build_topbar(self) -> QWidget:
        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(78)
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(22, 12, 22, 12)
        layout.setSpacing(7)

        brand_widget = QWidget()
        brand_widget.setFixedWidth(182)
        brand = QHBoxLayout(brand_widget)
        brand.setContentsMargins(0, 0, 0, 0)
        brand.setSpacing(10)
        brand.addWidget(RadarLogo(43))
        brand_copy = QVBoxLayout()
        brand_copy.setSpacing(0)
        name = QLabel("RADAR DESK")
        name.setObjectName("brandName")
        version = QLabel(f"SERVICE HUB  •  v{APP_VERSION}")
        version.setObjectName("brandVersion")
        brand_copy.addWidget(name)
        brand_copy.addWidget(version)
        brand.addLayout(brand_copy)
        layout.addWidget(brand_widget)
        layout.addSpacing(8)

        entries = [
            ("Visão geral", 0),
            ("Chamados", 1),
            ("Diagnóstico", 2),
            ("Relatórios", 3),
            ("Ajustes", 4),
        ]
        for label, index in entries:
            layout.addWidget(self._nav_button(label, index))

        layout.addStretch()
        offline = QLabel("●  Local")
        offline.setObjectName("offlineLabel")
        offline.setToolTip("Operação local ativa — nenhuma internet necessária")
        layout.addWidget(offline)

        self.theme_button = QToolButton()
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_button.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_button)
        return topbar

    def _nav_button(self, label: str, index: int) -> QPushButton:
        button = QPushButton(label)
        button.setProperty("topNav", True)
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda checked=False, page=index: self._select_page(page))
        self.nav_buttons.append(button)
        return button

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(86)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 14, 30, 14)

        copy = QVBoxLayout()
        copy.setSpacing(2)
        self.page_title = QLabel()
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel()
        self.page_subtitle.setObjectName("pageSubtitle")
        copy.addWidget(self.page_title)
        copy.addWidget(self.page_subtitle)
        layout.addLayout(copy, 1)

        return header

    def _add_page(self, title: str, subtitle: str, widget: QWidget) -> None:
        self.page_metadata.append((title, subtitle))
        self.pages.addWidget(widget)

    def _build_dashboard(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(18)

        hero = QFrame()
        hero.setProperty("card", True)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(26, 24, 26, 24)
        hero_layout.setSpacing(22)

        copy = QVBoxLayout()
        copy.setSpacing(8)
        eyebrow = QLabel("GESTÃO OPERACIONAL DISPONÍVEL")
        eyebrow.setObjectName("heroEyebrow")
        title = QLabel("Do registro à resolução, tudo fica rastreável.")
        title.setObjectName("heroTitle")
        title.setWordWrap(True)
        detail = QLabel(
            "Busque, filtre, atribua responsáveis e registre comentários. "
            "Cada alteração permanece no histórico local do chamado."
        )
        detail.setObjectName("heroText")
        detail.setWordWrap(True)
        copy.addWidget(eyebrow)
        copy.addWidget(title)
        copy.addWidget(detail)
        hero_layout.addLayout(copy, 1)
        hero_layout.addWidget(RadarLogo(104))
        layout.addWidget(hero)

        stats = QHBoxLayout()
        stats.setSpacing(14)
        self.total_card = StatCard(
            "Total de chamados", str(self.ticket_service.count_all()), "#2dd4bf"
        )
        self.active_card = StatCard(
            "Chamados ativos", str(self.ticket_service.count_active()), "#60a5fa"
        )
        self.version_card = StatCard("Versão instalada", f"v{APP_VERSION}", "#a78bfa")
        stats.addWidget(self.total_card)
        stats.addWidget(self.active_card)
        stats.addWidget(self.version_card)
        layout.addLayout(stats)

        roadmap = QFrame()
        roadmap.setProperty("card", True)
        roadmap_layout = QVBoxLayout(roadmap)
        roadmap_layout.setContentsMargins(20, 18, 20, 20)
        roadmap_layout.setSpacing(9)
        roadmap_title = QLabel("Próximas entregas")
        roadmap_title.setObjectName("sectionTitle")
        roadmap_layout.addWidget(roadmap_title)
        roadmap_layout.addWidget(RoadmapItem("1", "Base do aplicativo", "Janela, navegação, temas e SQLite", True))
        roadmap_layout.addWidget(RoadmapItem("2", "Cadastro de chamados", "CRUD local e protocolo automático", True))
        roadmap_layout.addWidget(RoadmapItem("3", "Gestão operacional", "Busca, filtros, histórico e interações", True))
        layout.addWidget(roadmap)
        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)
        return page

    def _build_coming_page(self, version: str, title: str, detail: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.addStretch()
        card = QFrame()
        card.setProperty("card", True)
        card.setMaximumWidth(680)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(34, 30, 34, 32)
        card_layout.setSpacing(12)
        badge = QLabel(f"VERSÃO {version}")
        badge.setObjectName("versionBadge")
        badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        heading = QLabel(title)
        heading.setObjectName("comingTitle")
        description = QLabel(detail)
        description.setProperty("muted", True)
        description.setWordWrap(True)
        description.setStyleSheet("font-size: 15px;")
        card_layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignLeft)
        card_layout.addWidget(heading)
        card_layout.addWidget(description)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(card)
        row.addStretch()
        layout.addLayout(row)
        layout.addStretch()
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(14)

        card = QFrame()
        card.setProperty("card", True)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 22)
        card_layout.setSpacing(8)
        heading = QLabel("Aparência")
        heading.setObjectName("sectionTitle")
        detail = QLabel("Use o botão no topo para alternar entre os modos claro e escuro.")
        detail.setProperty("muted", True)
        card_layout.addWidget(heading)
        card_layout.addWidget(detail)
        layout.addWidget(card)

        database_card = QFrame()
        database_card.setProperty("card", True)
        database_layout = QVBoxLayout(database_card)
        database_layout.setContentsMargins(22, 20, 22, 22)
        db_heading = QLabel("Armazenamento local")
        db_heading.setObjectName("sectionTitle")
        db_detail = QLabel(str(self.database.path))
        db_detail.setProperty("muted", True)
        db_detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        db_detail.setWordWrap(True)
        database_layout.addWidget(db_heading)
        database_layout.addWidget(db_detail)
        layout.addWidget(database_card)
        layout.addStretch()
        return page

    def _select_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)
        title, subtitle = self.page_metadata[index]
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)
        if index == 0:
            self._refresh_dashboard()

    def _refresh_dashboard(self) -> None:
        self.total_card.set_value(str(self.ticket_service.count_all()))
        self.active_card.set_value(str(self.ticket_service.count_active()))

    def _restore_theme(self) -> None:
        value = self.settings.value("appearance/theme", Theme.LIGHT.value)
        try:
            theme = Theme(str(value))
        except ValueError:
            theme = Theme.LIGHT
        self._apply_theme(theme)

    def _toggle_theme(self) -> None:
        next_theme = Theme.DARK if self.current_theme is Theme.LIGHT else Theme.LIGHT
        self._apply_theme(next_theme)
        self.settings.setValue("appearance/theme", next_theme.value)

    def _apply_theme(self, theme: Theme) -> None:
        self.current_theme = theme
        app = QApplication.instance()
        if app:
            app.setStyleSheet(stylesheet(theme))
        if theme is Theme.DARK:
            self.theme_button.setText("☀  Tema")
            self.theme_button.setToolTip("Ativar modo claro")
        else:
            self.theme_button.setText("☾  Tema")
            self.theme_button.setToolTip("Ativar modo escuro")
