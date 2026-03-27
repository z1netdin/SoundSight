"""User-friendly error handling - no crashes, no console errors.

Shows GUI dialogs with clear messages and recovery options.
"""

from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

DARK_STYLE = """
    QDialog, QMessageBox {
        background-color: #1a1a2e;
        color: #e0e0e8;
    }
    QLabel {
        color: #e0e0e8;
        font-size: 13px;
    }
    QPushButton {
        background-color: #2a2a4e;
        color: #e0e0e8;
        border: 1px solid #3a3a5e;
        padding: 8px 20px;
        border-radius: 4px;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #3a3a6e;
    }
    QPushButton:pressed {
        background-color: #1a1a3e;
    }
    QPushButton#primary {
        background-color: #00c853;
        color: #1a1a2e;
        border: none;
        font-weight: bold;
    }
    QPushButton#primary:hover {
        background-color: #00e676;
    }
"""


# Custom exceptions for audio capture
class DeviceNotFoundError(Exception):
    """No suitable audio loopback device was found."""
    pass


class WASAPINotAvailableError(Exception):
    """WASAPI is not available on this system."""
    pass


class AudioStreamError(Exception):
    """Failed to open audio stream."""
    pass


def show_error(title, message, detail=None):
    """Show a simple error dialog."""
    msg = QMessageBox()
    # Theme applied globally
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    if detail:
        msg.setInformativeText(detail)
    msg.exec_()


def show_warning(title, message):
    """Show a warning dialog."""
    msg = QMessageBox()
    # Theme applied globally
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec_()


def show_info(title, message):
    """Show an info dialog."""
    msg = QMessageBox()
    # Theme applied globally
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec_()


class ErrorRecoveryDialog(QDialog):
    """Error dialog with recovery options."""

    RETRY = 1
    SETUP = 2
    QUIT = 3

    def __init__(self, title, message, show_setup=True, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowCloseButtonHint
        )
        self.setMinimumWidth(400)
        self.setMaximumWidth(500)
        self.result_action = self.QUIT

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Error icon + message
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title_label.setStyleSheet("color: #ff6b6b;")
        layout.addWidget(title_label)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setFont(QFont("Segoe UI", 12))
        layout.addWidget(msg_label)

        layout.addSpacing(10)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        if show_setup:
            setup_btn = QPushButton("Run Setup Wizard")
            setup_btn.setProperty("class", "primary")
            setup_btn.clicked.connect(lambda: self._done(self.SETUP))
            btn_layout.addWidget(setup_btn)

        retry_btn = QPushButton("Try Again")
        retry_btn.clicked.connect(lambda: self._done(self.RETRY))
        btn_layout.addWidget(retry_btn)

        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(lambda: self._done(self.QUIT))
        btn_layout.addWidget(quit_btn)

        layout.addLayout(btn_layout)

    def _done(self, action):
        self.result_action = action
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        from .theme import apply_dark_titlebar
        apply_dark_titlebar(self)

    def get_action(self):
        self.exec_()
        return self.result_action
