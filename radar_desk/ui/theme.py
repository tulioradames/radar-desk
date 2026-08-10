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
"""


def stylesheet(theme: Theme) -> str:
    return DARK_STYLESHEET if theme is Theme.DARK else LIGHT_STYLESHEET
