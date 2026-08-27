"""Widgets visuais reutilizáveis."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class RadarLogo(QWidget):
    """Marca vetorial desenhada em tempo de execução, sem arquivos externos."""

    def __init__(self, size: int = 44, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)

    def paintEvent(self, event) -> None:  # noqa: N802 - API Qt
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) - 4
        bounds = QRectF(2, 2, side, side)
        center = bounds.center()

        painter.setBrush(QColor("#0f2d2c"))
        painter.setPen(QPen(QColor("#256c65"), 1))
        painter.drawEllipse(bounds)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#32c9b7"), 1.2))
        for ratio in (0.34, 0.65):
            diameter = side * ratio
            painter.drawEllipse(
                QRectF(
                    center.x() - diameter / 2,
                    center.y() - diameter / 2,
                    diameter,
                    diameter,
                )
            )

        painter.setPen(QPen(QColor("#5eead4"), 2.4))
        painter.drawLine(center, QPointF(bounds.right() - 5, bounds.top() + 8))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#99f6e4"))
        painter.drawEllipse(center, 2.8, 2.8)


class StatCard(QFrame):
    def __init__(self, label: str, value: str, accent: str, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("card", True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(112)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        marker = QFrame()
        marker.setFixedSize(5, 56)
        marker.setStyleSheet(f"background: {accent}; border-radius: 2px;")
        layout.addWidget(marker)

        text = QVBoxLayout()
        text.setSpacing(4)
        self.value_label = QLabel(value)
        self.value_label.setProperty("statValue", True)
        caption = QLabel(label)
        caption.setProperty("statLabel", True)
        caption.setWordWrap(True)
        text.addWidget(self.value_label)
        text.addWidget(caption)
        text.addStretch()
        layout.addLayout(text, 1)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class RoadmapItem(QFrame):
    def __init__(self, number: str, title: str, subtitle: str, done: bool = False) -> None:
        super().__init__()
        self.setObjectName("roadmapItem")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(13, 10, 13, 10)
        layout.setSpacing(12)

        badge = QLabel("✓" if done else number)
        badge.setObjectName("stepBadgeDone" if done else "stepBadgeNext")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFixedSize(24, 24)
        layout.addWidget(badge)

        copy = QVBoxLayout()
        copy.setSpacing(1)
        heading = QLabel(title)
        heading.setStyleSheet("font-weight: 650;")
        detail = QLabel(subtitle)
        detail.setProperty("muted", True)
        detail.setStyleSheet("font-size: 12px;")
        copy.addWidget(heading)
        copy.addWidget(detail)
        layout.addLayout(copy, 1)
