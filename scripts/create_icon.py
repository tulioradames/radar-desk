"""Gera os ícones PNG e ICO a partir da marca vetorial oficial."""

from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


ROOT = Path(__file__).resolve().parent.parent
SVG_PATH = ROOT / "radar_desk" / "resources" / "radar_desk.svg"
ICO_PATH = SVG_PATH.with_name("radar_desk.ico")
PNG_PATH = SVG_PATH.with_name("radar_desk.png")
SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)


def render(size: int, renderer: QSvgRenderer) -> Image.Image:
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    payload = QByteArray()
    buffer = QBuffer(payload)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return Image.open(BytesIO(bytes(payload))).convert("RGBA")


def main() -> int:
    renderer = QSvgRenderer(str(SVG_PATH))
    if not renderer.isValid():
        raise RuntimeError(f"Marca SVG inválida: {SVG_PATH}")
    images = [render(size, renderer) for size in SIZES]
    images[-1].save(PNG_PATH, "PNG", optimize=True)
    images[-1].save(
        ICO_PATH,
        format="ICO",
        append_images=images[:-1],
        sizes=[(size, size) for size in SIZES],
    )
    print(ICO_PATH)
    print(PNG_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
