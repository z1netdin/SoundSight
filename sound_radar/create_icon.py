"""Generate the SoundSight app icon.

Creates an eye-shaped icon with green sound wave curves.
Saves as .png files in multiple sizes.
"""

import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPainter, QColor, QPixmap, QIcon, QPen, QBrush, QRadialGradient, QPainterPath
from PyQt5.QtCore import Qt, QPointF


def create_icon(size=256):
    """Create SoundSight icon - eye made from sound waves."""
    import math

    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)

    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)

    cx, cy = size / 2, size / 2
    r = size * 0.45

    # Background circle - dark
    bg = QRadialGradient(cx, cy, r * 1.1)
    bg.setColorAt(0.0, QColor(14, 14, 24))
    bg.setColorAt(1.0, QColor(8, 8, 16))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(bg))
    p.drawEllipse(QPointF(cx, cy), r * 1.08, r * 1.08)

    # Outer ring
    p.setPen(QPen(QColor(0, 200, 100, 120), size * 0.015))
    p.setBrush(Qt.NoBrush)
    p.drawEllipse(QPointF(cx, cy), r * 1.02, r * 1.02)

    # Eye shape - two curved arcs forming an eye
    green = QColor(0, 230, 118)
    green_dim = QColor(0, 180, 90, 100)

    # Upper eyelid arc (sound wave 1)
    p.setPen(QPen(green, size * 0.025, Qt.SolidLine, Qt.RoundCap))
    eye_w = r * 1.6
    eye_h = r * 0.7
    upper = QPainterPath()
    upper.moveTo(cx - eye_w * 0.5, cy)
    upper.quadTo(cx, cy - eye_h, cx + eye_w * 0.5, cy)
    p.drawPath(upper)

    # Lower eyelid arc (sound wave 2)
    lower = QPainterPath()
    lower.moveTo(cx - eye_w * 0.5, cy)
    lower.quadTo(cx, cy + eye_h, cx + eye_w * 0.5, cy)
    p.drawPath(lower)

    # Outer sound wave arcs (thinner, dimmer)
    p.setPen(QPen(green_dim, size * 0.015, Qt.SolidLine, Qt.RoundCap))
    outer_h = r * 0.95
    outer1 = QPainterPath()
    outer1.moveTo(cx - eye_w * 0.55, cy)
    outer1.quadTo(cx, cy - outer_h, cx + eye_w * 0.55, cy)
    p.drawPath(outer1)

    outer2 = QPainterPath()
    outer2.moveTo(cx - eye_w * 0.55, cy)
    outer2.quadTo(cx, cy + outer_h, cx + eye_w * 0.55, cy)
    p.drawPath(outer2)

    # Iris - green circle in the center
    iris_r = r * 0.28
    iris_grad = QRadialGradient(cx, cy, iris_r)
    iris_grad.setColorAt(0.0, QColor(0, 255, 140, 200))
    iris_grad.setColorAt(0.6, QColor(0, 200, 100, 160))
    iris_grad.setColorAt(1.0, QColor(0, 160, 80, 60))
    p.setPen(QPen(green, size * 0.012))
    p.setBrush(QBrush(iris_grad))
    p.drawEllipse(QPointF(cx, cy), iris_r, iris_r)

    # Pupil - bright center dot
    pupil_r = r * 0.1
    pupil_grad = QRadialGradient(cx, cy, pupil_r)
    pupil_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
    pupil_grad.setColorAt(0.4, QColor(200, 255, 220, 200))
    pupil_grad.setColorAt(1.0, QColor(0, 230, 118, 100))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(pupil_grad))
    p.drawEllipse(QPointF(cx, cy), pupil_r, pupil_r)

    p.end()
    return pm


def save_icons():
    """Save icon in all needed formats and sizes."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    os.makedirs(assets_dir, exist_ok=True)

    # Generate multiple sizes
    sizes = [16, 24, 32, 48, 64, 128, 256]
    pixmaps = []

    for size in sizes:
        pm = create_icon(size)
        pm.save(os.path.join(assets_dir, f"icon_{size}.png"))
        pixmaps.append(pm)
        print(f"  Created icon_{size}.png")

    # Save main PNG
    main = create_icon(256)
    main.save(os.path.join(assets_dir, "icon.png"))
    print(f"  Created icon.png (256x256)")

    # Create .ico file (Windows icon with multiple sizes)
    # QIcon can save as ICO on Windows
    icon = QIcon()
    for pm in pixmaps:
        icon.addPixmap(pm)

    # Save ICO using the pixmaps
    ico_path = os.path.join(assets_dir, "icon.ico")

    # PyQt can't directly save .ico, so we'll use the 256px PNG
    # and convert it. For now save as PNG - build.bat can use it.
    print(f"\n  Icon files saved to: {assets_dir}")
    print(f"  Use icon.png for the app window and tray")


if __name__ == "__main__":
    save_icons()
