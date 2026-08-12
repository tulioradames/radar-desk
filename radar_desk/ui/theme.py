"""Temas claro e escuro da interface."""

from __future__ import annotations

from enum import StrEnum


class Theme(StrEnum):
    LIGHT = "light"
    DARK = "dark"


LIGHT_STYLESHEET = """
* {
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 14px;
}
QMainWindow, QWidget#appRoot, QStackedWidget#pageStack {
    background: #f4f7fb;
    color: #172033;
}
QFrame#topbar {
    background: #0b1220;
    border: none;
    border-bottom: 1px solid #1d2939;
}
QLabel#brandName {
    color: #f8fafc;
    font-size: 19px;
    font-weight: 700;
}
QLabel#brandVersion {
    color: #8290a7;
    font-size: 11px;
    font-weight: 600;
}
QPushButton[topNav="true"] {
    background: transparent;
    color: #9ca9bb;
    border: none;
    border-radius: 8px;
    padding: 10px 11px;
    text-align: center;
    font-weight: 600;
}
QPushButton[topNav="true"]:hover {
    background: #162033;
    color: #f8fafc;
}
QPushButton[topNav="true"]:checked {
    background: #11352f;
    color: #5eead4;
    border-bottom: 3px solid #2dd4bf;
}
QLabel#offlineLabel {
    color: #a7f3d0;
    background: #12352f;
    border: 1px solid #1b5147;
    border-radius: 8px;
    padding: 8px 11px;
    font-size: 12px;
}
QFrame#header {
    background: #ffffff;
    border-bottom: 1px solid #e5eaf1;
}
QLabel#pageTitle {
    color: #111827;
    font-size: 24px;
    font-weight: 700;
}
QLabel#pageSubtitle, QLabel[muted="true"] {
    color: #6b778c;
}
QToolButton#themeButton {
    background: #eef2f7;
    color: #344054;
    border: 1px solid #dfe5ed;
    border-radius: 9px;
    padding: 8px 12px;
    font-weight: 600;
}
QToolButton#themeButton:hover {
    background: #e2e8f0;
}
QFrame[card="true"] {
    background: #ffffff;
    border: 1px solid #e1e7ef;
    border-radius: 14px;
}
QLabel#heroEyebrow {
    color: #0f8f7f;
    font-size: 12px;
    font-weight: 700;
}
QLabel#heroTitle {
    color: #142033;
    font-size: 30px;
    font-weight: 750;
}
QLabel#heroText {
    color: #637086;
    font-size: 15px;
}
QLabel[statValue="true"] {
    color: #162033;
    font-size: 20px;
    font-weight: 700;
}
QLabel[statLabel="true"] {
    color: #778397;
    font-size: 12px;
}
QLabel#sectionTitle {
    color: #172033;
    font-size: 17px;
    font-weight: 700;
}
QFrame#roadmapItem {
    background: #f8fafc;
    border: 1px solid #e8edf3;
    border-radius: 10px;
}
QLabel#stepBadgeDone {
    color: #08796d;
    background: #ccfbf1;
    border-radius: 11px;
    font-weight: 700;
    min-width: 22px;
    min-height: 22px;
}
QLabel#stepBadgeNext {
    color: #475569;
    background: #e2e8f0;
    border-radius: 11px;
    font-weight: 700;
    min-width: 22px;
    min-height: 22px;
}
QLabel#comingTitle {
    color: #172033;
    font-size: 25px;
    font-weight: 700;
}
QLabel#versionBadge {
    color: #08796d;
    background: #ccfbf1;
    border: 1px solid #99f6e4;
    border-radius: 12px;
    padding: 5px 10px;
    font-weight: 700;
}
QDialog {
    background: #f8fafc;
    color: #172033;
}
QLabel#dialogTitle {
    color: #111827;
    font-size: 23px;
    font-weight: 700;
}
QFrame#divider {
    color: #e2e8f0;
    background: #e2e8f0;
    max-height: 1px;
}
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background: #ffffff;
    color: #172033;
    border: 1px solid #cfd8e5;
    border-radius: 8px;
    padding: 9px 10px;
    selection-background-color: #2dd4bf;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {
    border: 2px solid #14b8a6;
}
QComboBox::drop-down {
    border: none;
    width: 28px;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    color: #172033;
    border: 1px solid #cfd8e5;
    selection-background-color: #ccfbf1;
    selection-color: #0f766e;
}
QPushButton[primary="true"] {
    background: #0f9f8e;
    color: #ffffff;
    border: 1px solid #0d8b7d;
    border-radius: 8px;
    padding: 9px 15px;
    font-weight: 700;
}
QPushButton[primary="true"]:hover { background: #0d8b7d; }
QPushButton[secondary="true"] {
    background: #ffffff;
    color: #344054;
    border: 1px solid #cfd8e5;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton[secondary="true"]:hover { background: #f1f5f9; }
QPushButton[danger="true"] {
    background: #fff1f2;
    color: #be123c;
    border: 1px solid #fecdd3;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton[danger="true"]:hover { background: #ffe4e6; }
QPushButton:disabled {
    background: #eef2f6;
    color: #9aa5b4;
    border-color: #dfe5ed;
}
QLabel#formError {
    color: #b42318;
    background: #fef3f2;
    border: 1px solid #fecdca;
    border-radius: 8px;
    padding: 9px 11px;
}
QLabel#countBadge {
    color: #0f766e;
    background: #ccfbf1;
    border-radius: 12px;
    padding: 5px 10px;
    font-weight: 700;
}
QLabel#overdueBadge {
    color: #be123c;
    background: #fff1f2;
    border: 1px solid #fecdd3;
    border-radius: 12px;
    padding: 5px 10px;
    font-weight: 700;
}
QLabel#automationHint {
    color: #0f766e;
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
    border-radius: 7px;
    padding: 7px 9px;
}
QLabel#slaLabel {
    color: #166534;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 8px 9px;
    font-weight: 700;
}
QLabel#slaLabel[slaState="near_due"] {
    color: #92400e;
    background: #fffbeb;
    border-color: #fde68a;
}
QLabel#slaLabel[slaState="overdue"] {
    color: #be123c;
    background: #fff1f2;
    border-color: #fecdd3;
}
QLabel#slaLabel[slaState="completed"] {
    color: #475569;
    background: #f1f5f9;
    border-color: #cbd5e1;
}
QLabel#privacyNotice {
    color: #155e75;
    background: #ecfeff;
    border: 1px solid #a5f3fc;
    border-radius: 9px;
    padding: 9px 12px;
    font-weight: 600;
}
QLabel#screenshotPreview {
    color: #718096;
    background: #f8fafc;
    border: 1px dashed #b9c5d4;
    border-radius: 10px;
    padding: 8px;
}
QFrame#dropZone {
    background: #f0fdfa;
    border: 2px dashed #75d9ca;
    border-radius: 11px;
}
QFrame#dropZone:disabled {
    background: #f5f7fa;
    border-color: #cfd8e5;
}
QLabel#dropIcon {
    color: #0f9f8e;
    font-size: 24px;
    font-weight: 700;
}
QLabel#dropTitle {
    color: #22514b;
    font-weight: 700;
}
QListWidget#attachmentList {
    background: #ffffff;
    alternate-background-color: #f8fafc;
    color: #344054;
    border: 1px solid #e1e7ef;
    border-radius: 10px;
    outline: none;
}
QListWidget#attachmentList::item {
    border-bottom: 1px solid #edf1f5;
    padding: 10px 8px;
}
QListWidget#attachmentList::item:selected {
    background: #dff8f4;
    color: #124e48;
}
QScrollArea#imageScroll {
    background: #f8fafc;
    border: 1px solid #e1e7ef;
    border-radius: 11px;
}
QLabel#imagePreview {
    color: #718096;
    background: #f8fafc;
    padding: 12px;
}
QTableWidget {
    background: #ffffff;
    alternate-background-color: #f8fafc;
    color: #243247;
    border: none;
    border-radius: 13px;
    gridline-color: #e8edf3;
    selection-background-color: #dff8f4;
    selection-color: #102a2a;
}
QTableWidget::item {
    padding: 7px;
    border-bottom: 1px solid #edf1f5;
}
QHeaderView::section {
    background: #f4f7fa;
    color: #657288;
    border: none;
    border-bottom: 1px solid #dfe6ee;
    padding: 10px 8px;
    font-size: 12px;
    font-weight: 700;
}
QLabel#emptyIcon {
    color: #2dd4bf;
    font-size: 48px;
    font-weight: 300;
}
QLabel#emptyTitle {
    color: #172033;
    font-size: 18px;
    font-weight: 700;
}
QLabel#detailProtocol {
    color: #0f8f7f;
    font-size: 13px;
    font-weight: 700;
}
QLabel#detailTitle {
    color: #172033;
    font-size: 19px;
    font-weight: 700;
}
QLabel#detailDescription {
    color: #48566a;
    background: #f8fafc;
    border: 1px solid #e5eaf1;
    border-radius: 9px;
    padding: 11px;
}
QLabel#assigneeLabel {
    color: #334155;
    background: #eefbf8;
    border: 1px solid #c5eee7;
    border-radius: 8px;
    padding: 7px 9px;
    font-weight: 600;
}
QCheckBox {
    color: #48566a;
    spacing: 7px;
}
QTabWidget::pane {
    border: 1px solid #e1e7ef;
    border-radius: 9px;
    background: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background: #eef2f7;
    color: #667085;
    border: 1px solid #dfe5ed;
    padding: 8px 10px;
    font-size: 12px;
    font-weight: 650;
}
QTabBar::tab:first { border-top-left-radius: 7px; }
QTabBar::tab:last { border-top-right-radius: 7px; }
QTabBar::tab:selected {
    background: #ffffff;
    color: #0f8f7f;
    border-bottom-color: #ffffff;
}
QListWidget#interactionList {
    background: #ffffff;
    color: #344054;
    border: none;
    outline: none;
}
QListWidget#interactionList::item {
    border-bottom: 1px solid #edf1f5;
    padding: 9px 6px;
}
QScrollArea#detailScroll, QScrollArea#detailScroll > QWidget > QWidget {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 22px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover { background: #94a3b8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
"""


DARK_STYLESHEET = LIGHT_STYLESHEET + """
QMainWindow, QWidget#appRoot, QStackedWidget#pageStack {
    background: #0e1523;
    color: #e7edf7;
}
QFrame#topbar {
    background: #080d17;
}
QFrame#header {
    background: #121b2b;
    border-bottom: 1px solid #243044;
}
QLabel#pageTitle, QLabel#heroTitle, QLabel#sectionTitle,
QLabel[statValue="true"], QLabel#comingTitle {
    color: #edf2f8;
}
QLabel#pageSubtitle, QLabel[muted="true"], QLabel#heroText,
QLabel[statLabel="true"] {
    color: #91a0b5;
}
QToolButton#themeButton {
    background: #1c283a;
    color: #dce5f0;
    border: 1px solid #2b3a50;
}
QToolButton#themeButton:hover {
    background: #26354a;
}
QFrame[card="true"] {
    background: #121b2b;
    border: 1px solid #26344a;
}
QFrame#roadmapItem {
    background: #172235;
    border: 1px solid #29384e;
}
QLabel#stepBadgeNext {
    color: #b3c0d2;
    background: #2b394e;
}
QDialog {
    background: #0e1523;
    color: #e7edf7;
}
QLabel#dialogTitle, QLabel#emptyTitle, QLabel#detailTitle {
    color: #edf2f8;
}
QFrame#divider {
    color: #29384e;
    background: #29384e;
}
QLineEdit, QTextEdit, QComboBox, QDateEdit {
    background: #172235;
    color: #e7edf7;
    border-color: #34445b;
}
QComboBox QAbstractItemView {
    background: #172235;
    color: #e7edf7;
    border-color: #34445b;
    selection-background-color: #1f514b;
    selection-color: #ccfbf1;
}
QPushButton[secondary="true"] {
    background: #1c283a;
    color: #dce5f0;
    border-color: #34445b;
}
QPushButton[secondary="true"]:hover { background: #26354a; }
QPushButton[danger="true"] {
    background: #3b1c27;
    color: #fda4af;
    border-color: #6b293d;
}
QPushButton[danger="true"]:hover { background: #4a2130; }
QTableWidget {
    background: #121b2b;
    alternate-background-color: #152033;
    color: #dce5f0;
    gridline-color: #26344a;
    selection-background-color: #1e4a46;
    selection-color: #e6fffb;
}
QTableWidget::item { border-bottom-color: #26344a; }
QHeaderView::section {
    background: #172235;
    color: #9eacc0;
    border-bottom-color: #2b3a50;
}
QLabel#detailDescription {
    color: #b8c4d5;
    background: #172235;
    border-color: #29384e;
}
QLabel#assigneeLabel {
    color: #b9f5e9;
    background: #163530;
    border-color: #28574f;
}
QCheckBox { color: #b8c4d5; }
QLabel#overdueBadge {
    color: #fda4af;
    background: #3b1c27;
    border-color: #6b293d;
}
QLabel#automationHint {
    color: #a7f3d0;
    background: #15352f;
    border-color: #28574f;
}
QLabel#slaLabel {
    color: #bbf7d0;
    background: #15352f;
    border-color: #28574f;
}
QLabel#slaLabel[slaState="near_due"] {
    color: #fde68a;
    background: #3a3017;
    border-color: #665527;
}
QLabel#slaLabel[slaState="overdue"] {
    color: #fda4af;
    background: #3b1c27;
    border-color: #6b293d;
}
QLabel#slaLabel[slaState="completed"] {
    color: #cbd5e1;
    background: #1e293b;
    border-color: #475569;
}
QLabel#privacyNotice {
    color: #a5f3fc;
    background: #12303a;
    border-color: #245362;
}
QLabel#screenshotPreview {
    color: #9eacc0;
    background: #172235;
    border-color: #3a4b62;
}
QFrame#dropZone {
    background: #132f2c;
    border-color: #337c72;
}
QFrame#dropZone:disabled {
    background: #172235;
    border-color: #34445b;
}
QLabel#dropTitle { color: #b9f5e9; }
QListWidget#attachmentList {
    background: #121b2b;
    alternate-background-color: #152033;
    color: #d3dce8;
    border-color: #29384e;
}
QListWidget#attachmentList::item { border-bottom-color: #26344a; }
QListWidget#attachmentList::item:selected {
    background: #1e4a46;
    color: #e6fffb;
}
QScrollArea#imageScroll, QLabel#imagePreview {
    background: #101827;
    color: #9eacc0;
    border-color: #29384e;
}
QTabWidget::pane {
    border-color: #29384e;
    background: #121b2b;
}
QTabBar::tab {
    background: #172235;
    color: #9eacc0;
    border-color: #2b3a50;
}
QTabBar::tab:selected {
    background: #121b2b;
    color: #5eead4;
    border-bottom-color: #121b2b;
}
QListWidget#interactionList {
    background: #121b2b;
    color: #d3dce8;
}
QListWidget#interactionList::item { border-bottom-color: #26344a; }
"""


def stylesheet(theme: Theme) -> str:
    return DARK_STYLESHEET if theme is Theme.DARK else LIGHT_STYLESHEET
