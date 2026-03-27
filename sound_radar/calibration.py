"""Speaker Calibration - visually adjust where each speaker shows on screen.

User clicks a speaker, sees a bright flash on the edge, then clicks/drags
to move it to the correct position. Simple and visual.
"""

import math
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSlider,
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QFont, QPainter, QColor, QBrush, QPen

from .config import save_config


SPEAKERS = [
    ("Front Left (FL)", 0, "top"),
    ("Front Right (FR)", 1, "top"),
    ("Center (C)", 2, "top"),
    ("Side Right (SR)", 7, "right"),
    ("Rear Right (RR)", 5, "bottom"),
    ("Rear Left (RL)", 4, "bottom"),
    ("Side Left (SL)", 6, "left"),
]


class CalibrationOverlay(QWidget):
    """Full screen overlay that shows a bright marker at the current angle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.CrossCursor)
        self._dragging = False

        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        self.resize(screen.width(), screen.height())
        self.move(0, 0)

        self.marker_edge = "top"
        self.marker_pos = 0.5
        self.marker_visible = False

        # Click handler
        self.mouse_callback = None

    def set_marker(self, edge, pos):
        self.marker_edge = edge
        self.marker_pos = pos
        self.marker_visible = True
        self.update()

    def hide_marker(self):
        self.marker_visible = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w = self.width()
        h = self.height()

        # Fill entire screen with almost-invisible color so clicks register
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 1)))  # nearly invisible
        painter.drawRect(0, 0, w, h)

        # Visible borders on edges to show clickable area
        painter.setBrush(QBrush(QColor(0, 255, 140, 30)))
        border = 50
        painter.drawRect(0, 0, w, border)           # top
        painter.drawRect(0, h - border, w, border)   # bottom
        painter.drawRect(0, 0, border, h)             # left
        painter.drawRect(w - border, 0, border, h)    # right

        if not self.marker_visible:
            painter.end()
            return

        size = 30

        # Draw bright green marker at the position
        r, g, b = 0, 255, 140
        alpha = 220

        if self.marker_edge == "top":
            x = self.marker_pos * w
            y = size / 2
            # Glow
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(r, g, b, 60)))
            painter.drawEllipse(QPointF(x, y), size * 3, size * 3)
            # Core
            painter.setBrush(QBrush(QColor(r, g, b, alpha)))
            painter.drawEllipse(QPointF(x, y), size, size)
            # Line down
            painter.setPen(QPen(QColor(r, g, b, 100), 2))
            painter.drawLine(QPointF(x, size), QPointF(x, size * 4))

        elif self.marker_edge == "bottom":
            x = self.marker_pos * w
            y = h - size / 2
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(r, g, b, 60)))
            painter.drawEllipse(QPointF(x, y), size * 3, size * 3)
            painter.setBrush(QBrush(QColor(r, g, b, alpha)))
            painter.drawEllipse(QPointF(x, y), size, size)
            painter.setPen(QPen(QColor(r, g, b, 100), 2))
            painter.drawLine(QPointF(x, h - size), QPointF(x, h - size * 4))

        elif self.marker_edge == "left":
            x = size / 2
            y = self.marker_pos * h
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(r, g, b, 60)))
            painter.drawEllipse(QPointF(x, y), size * 3, size * 3)
            painter.setBrush(QBrush(QColor(r, g, b, alpha)))
            painter.drawEllipse(QPointF(x, y), size, size)
            painter.setPen(QPen(QColor(r, g, b, 100), 2))
            painter.drawLine(QPointF(size, y), QPointF(size * 4, y))

        elif self.marker_edge == "right":
            x = w - size / 2
            y = self.marker_pos * h
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(r, g, b, 60)))
            painter.drawEllipse(QPointF(x, y), size * 3, size * 3)
            painter.setBrush(QBrush(QColor(r, g, b, alpha)))
            painter.drawEllipse(QPointF(x, y), size, size)
            painter.setPen(QPen(QColor(r, g, b, 100), 2))
            painter.drawLine(QPointF(w - size, y), QPointF(w - size * 4, y))

        # No text - user controls from the dialog

        painter.end()

    def mousePressEvent(self, event):
        self._dragging = True
        if self.mouse_callback:
            self.mouse_callback(event.x(), event.y())

    def mouseMoveEvent(self, event):
        if self._dragging and self.mouse_callback:
            self.mouse_callback(event.x(), event.y())

    def mouseReleaseEvent(self, event):
        self._dragging = False


class CalibrationDialog(QDialog):
    """Dialog to calibrate speaker positions visually."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Speaker Calibration")
        self.setWindowFlags(
            Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint
        )
        self.setMinimumSize(400, 500)

        self.overlay = None
        self.current_speaker = None
        self.current_channel = None
        self.current_edge = None

        self._build_ui()

    def showEvent(self, event):
        super().showEvent(event)
        from .theme import apply_dark_titlebar
        apply_dark_titlebar(self)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Speaker Calibration")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)

        desc = QLabel(
            "Click a speaker below. A green dot appears on screen.\n"
            "Then click the screen edge where it should be.\n"
            "This adjusts the angle for that speaker."
        )
        desc.setStyleSheet("color: #9090a8;")
        layout.addWidget(desc)

        # Speaker buttons
        for speaker_name, channel, edge in SPEAKERS:
            btn = QPushButton(speaker_name)
            btn.clicked.connect(
                lambda checked, n=speaker_name, ch=channel, e=edge:
                self._start_calibrate(n, ch, e)
            )
            layout.addWidget(btn)

        self.status = QLabel("")
        self.status.setStyleSheet("color: #00e676; font-size: 12px;")
        layout.addWidget(self.status)

        # Position slider - drag to move the green dot
        pos_label = QLabel("Drag to move:")
        pos_label.setStyleSheet("color: #9090a8;")
        layout.addWidget(pos_label)

        self.pos_slider = QSlider(Qt.Horizontal)
        self.pos_slider.setRange(0, 1000)
        self.pos_slider.setValue(500)
        self.pos_slider.valueChanged.connect(self._on_slider_move)
        layout.addWidget(self.pos_slider)

        self.angle_label = QLabel("")
        self.angle_label.setStyleSheet("color: #00e676;")
        layout.addWidget(self.angle_label)

        # Done button
        done_btn = QPushButton("Done")
        done_btn.setProperty("class", "primary")
        done_btn.clicked.connect(self._finish)
        layout.addWidget(done_btn)

    def _start_calibrate(self, name, channel, edge):
        """Show the marker for this speaker and wait for click."""
        self.current_speaker = name
        self.current_channel = channel
        self.current_edge = edge

        # Get current angle
        from .audio_analyzer import CHANNEL_ANGLES_71
        angle = CHANNEL_ANGLES_71.get(channel, 0)

        # Calculate current position
        edges = {
            "top": (315, 405),
            "right": (60, 120),
            "bottom": (125, 235),
            "left": (240, 300),
        }
        start, end = edges[edge]
        adj_angle = angle
        if angle < start and edge == "top":
            adj_angle = angle + 360
        pos = (adj_angle - start) / (end - start)
        pos = max(0, min(1, pos))

        # Show overlay
        if self.overlay is None:
            self.overlay = CalibrationOverlay()
        self.overlay.mouse_callback = self._on_click
        self.overlay.set_marker(edge, pos)
        self.overlay.show()

        # Set slider to current position
        self.pos_slider.blockSignals(True)
        self.pos_slider.setValue(int(pos * 1000))
        self.pos_slider.blockSignals(False)
        self.angle_label.setText(f"{name}: {angle} degrees")
        self.status.setText(f"Drag the slider to move {name}")

    def _on_slider_move(self, value):
        """Slider dragged - move the marker in real-time."""
        if self.current_channel is None:
            return

        # Slider 0-1000 maps to the edge range
        edges = {
            "top": (315, 405),
            "right": (60, 120),
            "bottom": (125, 235),
            "left": (240, 300),
        }
        start, end = edges[self.current_edge]
        pos = value / 1000.0

        # Convert slider position to angle
        new_angle = start + pos * (end - start)
        if new_angle >= 360:
            new_angle -= 360

        # Update angle
        from . import audio_analyzer
        audio_analyzer.CHANNEL_ANGLES_71[self.current_channel] = round(new_angle, 1)

        # Update marker on screen
        if self.overlay:
            self.overlay.set_marker(self.current_edge, pos)

        self.angle_label.setText(f"{self.current_speaker}: {round(new_angle, 1)} degrees")

    def _move_marker(self, degrees):
        """Move the current speaker's angle by degrees."""
        if self.current_channel is None:
            return

        from . import audio_analyzer
        current = audio_analyzer.CHANNEL_ANGLES_71.get(self.current_channel, 0)
        new_angle = (current + degrees) % 360
        audio_analyzer.CHANNEL_ANGLES_71[self.current_channel] = round(new_angle, 1)

        # Update marker position
        edges = {
            "top": (315, 405),
            "right": (60, 120),
            "bottom": (125, 235),
            "left": (240, 300),
        }
        start, end = edges[self.current_edge]
        adj = new_angle
        if new_angle < start and self.current_edge == "top":
            adj = new_angle + 360
        pos = max(0, min(1, (adj - start) / (end - start)))

        if self.overlay:
            self.overlay.set_marker(self.current_edge, pos)

        self.status.setText(f"{self.current_speaker}: {round(new_angle, 1)} degrees")

    def _on_click(self, x, y):
        """User clicked the screen - update the angle."""
        if self.current_edge is None:
            return

        w = self.overlay.width()
        h = self.overlay.height()

        edges = {
            "top": (315, 405),
            "right": (60, 120),
            "bottom": (125, 235),
            "left": (240, 300),
        }
        start, end = edges[self.current_edge]

        # Convert click position to angle
        if self.current_edge == "top":
            pos = x / w
            new_angle = start + pos * (end - start)
            if new_angle >= 360:
                new_angle -= 360
        elif self.current_edge == "bottom":
            pos = x / w
            new_angle = start + pos * (end - start)
        elif self.current_edge == "right":
            pos = y / h
            new_angle = start + pos * (end - start)
        elif self.current_edge == "left":
            pos = y / h
            new_angle = start + pos * (end - start)
        else:
            return

        # Update the angle
        from . import audio_analyzer
        audio_analyzer.CHANNEL_ANGLES_71[self.current_channel] = round(new_angle, 1)

        # Show updated marker
        if self.current_edge in ("top", "bottom"):
            self.overlay.set_marker(self.current_edge, x / w)
        else:
            self.overlay.set_marker(self.current_edge, y / h)

        # Update slider to match
        edges_range = {
            "top": (315, 405),
            "right": (60, 120),
            "bottom": (125, 235),
            "left": (240, 300),
        }
        s, e = edges_range[self.current_edge]
        adj = new_angle
        if new_angle < s and self.current_edge == "top":
            adj = new_angle + 360
        slider_pos = int(((adj - s) / (e - s)) * 1000)
        self.pos_slider.blockSignals(True)
        self.pos_slider.setValue(max(0, min(1000, slider_pos)))
        self.pos_slider.blockSignals(False)

        self.angle_label.setText(f"{self.current_speaker}: {round(new_angle, 1)} degrees")
        self.status.setText(f"Drag on screen or use slider")

    def _finish(self):
        """Save all angles and close."""
        from . import audio_analyzer

        # Save angles to config
        angles = {}
        for ch, angle in audio_analyzer.CHANNEL_ANGLES_71.items():
            if angle is not None:
                angles[str(ch)] = angle
        self.config["channel_angles"] = angles
        save_config(self.config)

        if self.overlay:
            self.overlay.hide()
            self.overlay = None

        # Save angles to config and rebuild channel maps instantly
        from . import audio_analyzer
        angles = {}
        for ch, angle in audio_analyzer.CHANNEL_ANGLES_71.items():
            if angle is not None:
                angles[str(ch)] = angle
        self.config["channel_angles"] = angles
        save_config(self.config)

        # Rebuild channel influence maps so changes apply immediately
        if hasattr(audio_analyzer, '_active_analyzer') and audio_analyzer._active_analyzer:
            audio_analyzer._active_analyzer._build_channel_maps()

        self.status.setText("Saved and applied!")
        self.accept()
