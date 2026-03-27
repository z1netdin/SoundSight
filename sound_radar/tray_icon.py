"""System tray icon - always accessible, even when overlay is hidden."""

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt


def create_tray_icon_pixmap():
    """Create a simple green radar icon programmatically."""
    size = 64
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)

    painter = QPainter(pm)
    painter.setRenderHint(QPainter.Antialiasing)

    # Dark circle background
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(20, 20, 35))
    painter.drawEllipse(2, 2, size - 4, size - 4)

    # Green border
    painter.setPen(QColor(0, 255, 140))
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(4, 4, size - 8, size - 8)

    # Cross
    cx, cy = size // 2, size // 2
    painter.setPen(QColor(0, 200, 100, 100))
    painter.drawLine(cx, 8, cx, size - 8)
    painter.drawLine(8, cy, size - 8, cy)

    # Green wedge (sound indicator)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(0, 255, 140, 150))
    from PyQt5.QtGui import QPainterPath
    path = QPainterPath()
    path.moveTo(cx, cy)
    path.arcTo(8, 8, size - 16, size - 16, 60, 60)
    path.lineTo(cx, cy)
    painter.drawPath(path)

    # Center dot
    painter.setBrush(QColor(255, 255, 255))
    painter.drawEllipse(cx - 3, cy - 3, 6, 6)

    painter.end()
    return pm


class TrayIcon(QSystemTrayIcon):
    """System tray icon with quick access menu."""

    def __init__(self, overlay, config, settings_panel_class, parent=None):
        super().__init__(parent)
        self.overlay = overlay
        self.config = config
        self.settings_panel_class = settings_panel_class
        self._settings_panel = None

        # Use the app icon for tray
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            pixmap = create_tray_icon_pixmap()
            self.setIcon(QIcon(pixmap))
        self.setToolTip("SoundSight")

        # Build menu
        menu = QMenu()
        # Theme applied globally via APP_STYLESHEET
        menu.setStyleSheet("""
            QMenu {
                background-color: #151525;
                color: #e8e8f0;
                border: 1px solid #2a2a45;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #252545;
            }
            QMenu::separator {
                height: 1px;
                background: #2a2a45;
                margin: 4px 8px;
            }
        """)

        show_action = menu.addAction("Show / Hide Overlay")
        show_action.triggered.connect(self.overlay.toggle_visibility)

        menu.addSeparator()

        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self._open_settings)

        restart_action = menu.addAction("Restart")
        restart_action.triggered.connect(self._restart_app)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activate)

    def _restart_app(self):
        """Restart the entire application."""
        import sys, subprocess
        subprocess.Popen([sys.executable, "-m", "sound_radar"] + sys.argv[1:])
        QApplication.quit()

    def _on_activate(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._open_settings()

    def _open_settings(self):
        if self._settings_panel is None or not self._settings_panel.isVisible():
            self._settings_panel = self.settings_panel_class(
                self.config, self.overlay
            )
            self._settings_panel.show()
        else:
            self._settings_panel.raise_()
            self._settings_panel.activateWindow()
