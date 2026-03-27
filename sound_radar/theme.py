"""SoundSight - dark theme styling.

Applies dark title bar and consistent styling across the app.
"""

import ctypes
from ctypes import wintypes


def apply_dark_titlebar(window):
    """Make a window's title bar dark on Windows 10/11."""
    try:
        hwnd = int(window.winId())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )
    except Exception:
        pass

# Color palette
BG_DARKEST = "#08080f"
BG_DARK = "#0c0c16"
BG_MAIN = "#10101c"
BG_CARD = "#161628"
BG_INPUT = "#1c1c32"
BG_HOVER = "#24244a"
BG_ACTIVE = "#2e2e5a"

ACCENT = "#00e676"
ACCENT_DIM = "#00c853"
ACCENT_GLOW = "#00ff88"
ACCENT_BG = "#00e67615"  # accent with transparency

TEXT_PRIMARY = "#eeeef4"
TEXT_SECONDARY = "#9090a8"
TEXT_DIM = "#606078"

BORDER = "#28283e"
BORDER_LIGHT = "#34345a"
ERROR = "#ff4444"
WARNING = "#ffab00"
SUCCESS = "#00e676"


APP_STYLESHEET = f"""
    /* === Global Reset === */
    * {{
        outline: none;
    }}
    QWidget {{
        background-color: {BG_MAIN};
        color: {TEXT_PRIMARY};
        font-family: "Segoe UI", "SF Pro Display", system-ui, sans-serif;
        font-size: 12px;
        selection-background-color: {ACCENT};
        selection-color: {BG_DARKEST};
    }}

    /* === Windows === */
    QDialog, QWizard, QWizardPage {{
        background-color: {BG_DARK};
    }}
    QMainWindow {{
        background-color: {BG_DARK};
    }}

    /* === Buttons === */
    QPushButton {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        padding: 8px 14px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 500;
        min-height: 18px;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        border-color: {BORDER_LIGHT};
    }}
    QPushButton:pressed {{
        background-color: {BG_ACTIVE};
        border-color: {ACCENT_DIM};
    }}
    QPushButton:disabled {{
        color: {TEXT_DIM};
        background-color: {BG_CARD};
        border-color: {BG_CARD};
    }}
    QPushButton[class="primary"] {{
        background-color: {ACCENT};
        color: {BG_DARKEST};
        border: none;
        font-weight: 700;
        font-size: 11px;
        padding: 8px 18px;
    }}
    QPushButton[class="primary"]:hover {{
        background-color: {ACCENT_GLOW};
    }}
    QPushButton[class="primary"]:pressed {{
        background-color: {ACCENT_DIM};
    }}

    /* === Tabs === */
    QTabWidget {{
        background-color: {BG_DARK};
    }}
    QTabWidget::pane {{
        background-color: {BG_DARK};
        border: none;
        border-top: 1px solid {BORDER};
        padding-top: 4px;
    }}
    QTabBar {{
        background-color: transparent;
        min-height: 44px;
    }}
    QTabBar::tab {{
        background-color: transparent;
        color: {TEXT_DIM};
        padding: 8px 20px 8px 20px;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: 11px;
        font-weight: 600;
        margin-right: 2px;
        margin-top: 6px;
    }}
    QTabBar::tab:hover {{
        color: {TEXT_SECONDARY};
    }}
    QTabBar::tab:selected {{
        color: {ACCENT};
        border-bottom-color: {ACCENT};
    }}

    /* === Lists === */
    QListWidget {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 6px;
        outline: none;
        font-size: 13px;
    }}
    QListWidget::item {{
        padding: 10px 14px;
        border-radius: 6px;
        margin: 2px;
        min-height: 20px;
    }}
    QListWidget::item:hover {{
        background-color: {BG_HOVER};
    }}
    QListWidget::item:selected {{
        background-color: {ACCENT};
        color: {BG_DARKEST};
    }}

    /* === Sliders === */
    QSlider::groove:horizontal {{
        background: {BG_INPUT};
        height: 4px;
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {ACCENT};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {ACCENT_GLOW};
    }}
    QSlider::sub-page:horizontal {{
        background: {ACCENT};
        height: 4px;
        border-radius: 2px;
    }}

    /* === Combo Box === */
    QComboBox {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        padding: 10px 14px;
        border-radius: 8px;
        font-size: 12px;
        min-height: 22px;
    }}
    QComboBox:hover {{
        border-color: {BORDER_LIGHT};
    }}
    QComboBox:focus {{
        border-color: {ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        width: 0;
        height: 0;
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        selection-background-color: {BG_HOVER};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 4px;
    }}

    /* === Group Box === */
    QGroupBox {{
        color: {TEXT_SECONDARY};
        border: 1px solid {BORDER};
        border-radius: 10px;
        margin-top: 20px;
        padding: 28px 14px 14px 14px;
        font-size: 11px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 4px 12px;
        color: {TEXT_SECONDARY};
    }}

    /* === Tree Widget (profile tables) === */
    QTreeWidget {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 4px;
        outline: none;
        font-size: 11px;
    }}
    QTreeWidget::item {{
        padding: 10px 8px;
        border-radius: 4px;
    }}
    QTreeWidget::item:hover {{
        background-color: {BG_HOVER};
    }}
    QTreeWidget::item:selected {{
        background-color: {ACCENT};
        color: {BG_DARKEST};
    }}
    QHeaderView::section {{
        background-color: {BG_CARD};
        color: {TEXT_SECONDARY};
        border: none;
        border-bottom: 1px solid {BORDER};
        padding: 6px 8px;
        font-size: 10px;
        font-weight: 600;
    }}

    /* === Labels === */
    QLabel {{
        color: {TEXT_PRIMARY};
        background: transparent;
    }}

    /* === Scroll Bars === */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 4px 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {TEXT_DIM};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: transparent;
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER};
        border-radius: 4px;
        min-width: 30px;
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* === Text Edit === */
    QTextEdit {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 12px;
        font-size: 13px;
    }}

    /* === Menu === */
    QMenu {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 8px;
    }}
    QMenu::item {{
        padding: 10px 28px;
        border-radius: 6px;
        margin: 2px;
    }}
    QMenu::item:selected {{
        background-color: {BG_HOVER};
    }}
    QMenu::separator {{
        height: 1px;
        background: {BORDER};
        margin: 6px 12px;
    }}

    /* === Message Box === */
    QMessageBox {{
        background-color: {BG_DARK};
    }}
    QMessageBox QLabel {{
        color: {TEXT_PRIMARY};
        font-size: 13px;
    }}

    /* === Tool Tip === */
    QToolTip {{
        background-color: {BG_CARD};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 12px;
    }}

    /* === Wizard buttons === */
    QWizard QPushButton {{
        min-width: 80px;
    }}
"""
