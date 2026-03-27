"""Settings Panel - proper GUI for all settings.

Dark themed dialog with sidebar navigation for Audio, Appearance, Performance, and About.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QSlider, QComboBox, QListWidget, QListWidgetItem,
    QColorDialog, QFileDialog, QGroupBox, QGridLayout, QFrame, QLineEdit,
    QInputDialog, QTreeWidget, QTreeWidgetItem, QHeaderView,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap, QPainter, QPen, QBrush, QPainterPath

from .config import save_config
from . import profiles as prof

PANEL_STYLE = """
    * {
        font-family: 'Segoe UI', 'Arial', sans-serif;
        font-size: 13px;
    }
    QDialog {
        background-color: #111118;
        color: #e8e8f0;
    }

    /* Labels */
    QLabel {
        color: #c0c0d4;
        font-size: 13px;
        background: transparent;
        line-height: 1.4;
    }

    /* Buttons */
    QPushButton {
        background-color: #1c1c30;
        color: #c8c8d8;
        border: 1px solid #2c2c48;
        padding: 9px 20px;
        border-radius: 6px;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #242440;
        border-color: #00e676;
        color: #e8e8f0;
    }
    QPushButton:pressed {
        background-color: #00c853;
        color: #0a0a14;
        border-color: #00c853;
    }

    /* Dropdowns */
    QComboBox {
        background-color: #16162a;
        color: #e0e0e8;
        border: 1px solid #2c2c48;
        padding: 9px 40px 9px 14px;
        border-radius: 6px;
        font-size: 13px;
        min-height: 18px;
    }
    QComboBox:hover {
        border-color: #3c3c60;
    }
    QComboBox:on {
        border-color: #00e676;
    }
    QComboBox::drop-down {
        border: none;
        width: 0px;
        padding: 0;
    }
    QComboBox::down-arrow {
        image: none;
        width: 0; height: 0;
    }
    QComboBox QAbstractItemView {
        background-color: #16162a;
        color: #d0d0e0;
        border: 1px solid #2c2c48;
        padding: 4px;
        outline: none;
        selection-background-color: #00c853;
        selection-color: #000000;
    }
    QComboBox QAbstractItemView::item {
        padding: 8px 14px;
        min-height: 24px;
    }
    QComboBox QAbstractItemView::item:hover,
    QComboBox QAbstractItemView::item:selected {
        background-color: #00c853;
        color: #000000;
    }

    /* Sliders */
    QSlider {
    }
    QSlider::groove:horizontal {
        background: #1c1c30;
        height: 6px;
        border-radius: 3px;
    }
    QSlider::sub-page:horizontal {
        background: #00c853;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #00e676;
        width: 16px;
        height: 16px;
        margin: -5px 0;
        border-radius: 8px;
    }
    QSlider::handle:horizontal:hover {
        background: #44ffaa;
    }

    /* Lists */
    QListWidget {
        background-color: #16162a;
        color: #d0d0e0;
        border: 1px solid #2c2c48;
        border-radius: 6px;
        font-size: 12px;
    }
    QListWidget::item {
        padding: 8px 12px;
    }
    QListWidget::item:selected {
        background-color: #222240;
        color: #00e676;
    }
    QListWidget::item:hover {
        background-color: #1c1c34;
    }

    /* Group Boxes */
    QGroupBox {
        color: #b8b8c8;
        border: none;
        margin: 0; padding: 0;
        font-size: 12px;
    }
    QGroupBox::title {
        color: transparent;
    }

    /* Scroll Bars */
    QScrollBar:vertical {
        background: #111118;
        width: 8px;
        border: none;
    }
    QScrollBar::handle:vertical {
        background: #2c2c48;
        border-radius: 4px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: #3c3c60;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
"""


class SettingsPanel(QDialog):
    """Main settings dialog."""

    settings_changed = pyqtSignal()

    def __init__(self, config, overlay=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.overlay = overlay
        self.setWindowTitle("SoundSight")
        self.setStyleSheet(PANEL_STYLE)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        self.setMinimumSize(900, 600)
        self.resize(1050, 720)

        from .theme import apply_dark_titlebar
        self.show()
        apply_dark_titlebar(self)
        self.hide()

        # Outer layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Header bar with app name
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("background-color: #0c0c14; border-bottom: 1px solid #1c1c30;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        app_title = QLabel("SoundSight")
        app_title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        app_title.setStyleSheet("color: #00e676; background: transparent; border: none; font-size: 20px;")
        header_layout.addWidget(app_title)

        app_subtitle = QLabel("Visual Sound Radar")
        app_subtitle.setFont(QFont("Segoe UI", 11))
        app_subtitle.setStyleSheet("color: #606080; background: transparent; border: none;")
        header_layout.addWidget(app_subtitle)
        header_layout.addStretch()

        outer.addWidget(header)

        # Sidebar + Content layout
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #0c0c14;
                border-right: 1px solid #1c1c30;
            }
            QPushButton {
                text-align: left;
                padding: 16px 28px;
                font-size: 14px;
                border: none;
                border-radius: 0;
                background: transparent;
                color: #6a6a88;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: #14142a;
                color: #c0c0d8;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 8, 0, 0)
        sidebar_layout.setSpacing(0)

        # Page stack
        from PyQt5.QtWidgets import QStackedWidget
        self.page_stack = QStackedWidget()
        self.page_stack.setStyleSheet("QStackedWidget { background-color: #111118; }")

        pages = [
            ("Audio", self._build_audio_tab()),
            ("Appearance", self._build_appearance_tab()),
            ("Performance", self._build_performance_tab()),
            ("About", self._build_about_tab()),
        ]

        self._nav_buttons = []
        for i, (name, page) in enumerate(pages):
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self._switch_page(idx))
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)
            self.page_stack.addWidget(page)

        sidebar_layout.addStretch()
        self._switch_page(0)

        body_layout.addWidget(sidebar)

        # Right content area - centered horizontally, top-aligned with padding
        content = QWidget()
        content.setStyleSheet("QWidget { background-color: #111118; }")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Page content with max width so it doesn't stretch on maximize
        page_wrapper = QWidget()
        page_wrapper.setMaximumWidth(900)
        pw_layout = QVBoxLayout(page_wrapper)
        pw_layout.setContentsMargins(0, 0, 0, 0)
        pw_layout.addWidget(self.page_stack)

        content_layout.setContentsMargins(40, 30, 40, 20)
        content_layout.addWidget(page_wrapper)

        body_layout.addWidget(content)
        outer.addWidget(body)

        # Load heavy stuff after window is visible (not during construction)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(50, self._deferred_load)

    def _switch_page(self, index):
        """Switch sidebar page and highlight active button."""
        self.page_stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left; padding: 16px 28px; font-size: 14px;
                        border: none; border-left: 3px solid #00e676;
                        background: #141428; color: #00e676;
                        letter-spacing: 0.5px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        text-align: left; padding: 16px 28px; font-size: 14px;
                        border: none; border-radius: 0;
                        background: transparent; color: #6a6a88;
                        letter-spacing: 0.5px;
                    }
                    QPushButton:hover { background: #14142a; color: #c0c0d8; }
                """)

    def _deferred_load(self):
        """Load audio devices and volume after window appears."""
        self.device_combo.clear()
        self.device_combo.addItem("Scanning audio devices...")
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self._do_load)

    def _do_load(self):
        self._refresh_devices()
        self._init_volume()

    def _build_audio_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(6)
        layout.setContentsMargins(20, 24, 20, 20)

        heading = QLabel("Audio Device")
        heading.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(heading)

        input_desc = QLabel("Where SoundSight captures game audio from")
        input_desc.setStyleSheet("color: #6a6a84; font-size: 12px;")
        layout.addWidget(input_desc)

        layout.addSpacing(8)

        self.device_combo = QComboBox()
        
        self.device_combo.addItem("Loading...")
        layout.addWidget(self.device_combo)

        layout.addSpacing(6)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Apply Device")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #00c853; color: #0a0a1a; border: none;
                font-weight: bold; font-size: 13px; padding: 11px 26px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #00e676; }
            QPushButton:pressed { background-color: #009940; }
        """)
        apply_btn.clicked.connect(self._apply_device)
        btn_row.addWidget(apply_btn)

        calibrate_btn = QPushButton("Calibrate Speakers (7.1 only)")
        calibrate_btn.setStyleSheet("""
            QPushButton {
                background-color: #22223e; color: #d0d0e0;
                border: 1px solid #3a3a58; padding: 10px 22px;
                border-radius: 8px; font-size: 12px;
            }
            QPushButton:hover { background-color: #2e2e52; border-color: #00e676; color: #00e676; }
            QPushButton:pressed { background-color: #00c853; color: #0a0a1a; }
        """)
        calibrate_btn.clicked.connect(self._calibrate_speakers)
        btn_row.addWidget(calibrate_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.device_info = QLabel("")
        layout.addWidget(self.device_info)

        layout.addSpacing(10)

        # Volume control
        self._build_volume_section(layout)

        layout.addStretch()
        return tab

    def _refresh_devices(self):
        self.device_combo.clear()
        try:
            import pyaudiowpatch as pyaudio
            pa = pyaudio.PyAudio()
            current = self.config.get("audio_device")

            for i in range(pa.get_device_count()):
                dev = pa.get_device_info_by_index(i)
                if not dev.get("isLoopbackDevice", False):
                    continue
                ch = dev["maxInputChannels"]
                name = dev["name"]
                label = f"{name} - {ch}ch"
                if ch >= 8:
                    label += " (7.1)"
                self.device_combo.addItem(label, i)

                if i == current:
                    self.device_combo.setCurrentIndex(self.device_combo.count() - 1)

            pa.terminate()
        except Exception as e:
            self.device_combo.addItem(f"Error: {e}", -1)

    def _apply_device(self):
        idx = self.device_combo.currentData()
        if idx is not None and idx >= 0:
            self.config["audio_device"] = idx
            save_config(self.config)
            self.device_info.setText(
                "Device saved. Restart SoundSight to apply."
            )
            self.device_info.setStyleSheet("color: #00e676;")

    def _build_volume_section(self, layout):
        """Output device and volume."""
        layout.addSpacing(20)

        out_heading = QLabel("Output Device")
        out_heading.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(out_heading)

        out_desc = QLabel("Where you hear game audio")
        out_desc.setStyleSheet("color: #6a6a84; font-size: 12px;")
        layout.addWidget(out_desc)

        layout.addSpacing(8)

        self.output_combo = QComboBox()
        
        self.output_combo.addItem("Loading...")
        self.output_combo.currentIndexChanged.connect(self._on_output_device_changed)
        layout.addWidget(self.output_combo)

        layout.addSpacing(16)

        # Volume
        vol_row = QHBoxLayout()
        vol_label = QLabel("Volume")
        vol_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        vol_label.setMinimumWidth(65)
        vol_row.addWidget(vol_label)

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        
        self.vol_slider.valueChanged.connect(self._on_volume_change)
        vol_row.addWidget(self.vol_slider)

        self.vol_label = QLabel("--")
        self.vol_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.vol_label.setStyleSheet("color: #00e676;")
        self.vol_label.setMinimumWidth(50)
        vol_row.addWidget(self.vol_label)
        vol_row.addStretch()
        layout.addLayout(vol_row)

        # Volume loaded in _deferred_load()

    def _init_volume(self):
        """List all devices with volume control."""
        self._volume_ctrl = None
        self._vol_devices = []  # list of (name, IAudioEndpointVolume)

        self.output_combo.blockSignals(True)
        self.output_combo.clear()
        try:
            from pycaw.pycaw import AudioUtilities

            from pycaw.pycaw import AudioDeviceState
            devices = AudioUtilities.GetAllDevices()
            for dev in devices:
                if dev.state == AudioDeviceState.Active and dev.FriendlyName:
                    try:
                        vol = dev.EndpointVolume
                        if vol is not None:
                            self._vol_devices.append((dev.FriendlyName, vol))
                            self.output_combo.addItem(dev.FriendlyName)
                    except Exception:
                        continue

            if self._vol_devices:
                self.output_combo.setCurrentIndex(0)
                self.output_combo.blockSignals(False)
                self._select_output_volume(0)
            else:
                self.output_combo.addItem("No output devices")
                self.output_combo.blockSignals(False)
                self.vol_label.setText("N/A")
        except Exception as e:
            self.output_combo.addItem("Not available")
            self.output_combo.blockSignals(False)
            self.vol_label.setText("N/A")

    def _select_output_volume(self, index):
        """Set volume control to the selected device."""
        if index < 0 or index >= len(self._vol_devices):
            return
        name, vol = self._vol_devices[index]
        self._volume_ctrl = vol
        try:
            current = int(vol.GetMasterVolumeLevelScalar() * 100)
            self.vol_slider.blockSignals(True)
            self.vol_slider.setValue(current)
            self.vol_slider.blockSignals(False)
            self.vol_label.setText(f"{current}%")
        except Exception as e:
            self.vol_label.setText("N/A")

    def _on_output_device_changed(self, index):
        """Switch volume control to the selected device."""
        self._select_output_volume(index)

    def _on_volume_change(self, val):
        self.vol_label.setText(f"{val}%")
        if self._volume_ctrl is not None:
            try:
                self._volume_ctrl.SetMasterVolumeLevelScalar(val / 100.0, None)
            except Exception:
                pass

    def _build_appearance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(6)
        layout.setContentsMargins(20, 24, 20, 20)

        # Indicator settings
        layout.addSpacing(20)
        line_heading = QLabel("Indicator")
        line_heading.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(line_heading)

        line_desc = QLabel("Adjust the size of the edge indicator")
        line_desc.setStyleSheet("color: #6a6a84; font-size: 12px;")
        layout.addWidget(line_desc)

        layout.addSpacing(8)

        # Thickness
        thick_row = QHBoxLayout()
        thick_label = QLabel("Thickness")
        thick_label.setMinimumWidth(80)
        thick_row.addWidget(thick_label)
        self.thick_slider = QSlider(Qt.Horizontal)
        self.thick_slider.setRange(2, 20)
        self.thick_slider.setValue(self.config.get("line_thick", 14))
        
        self.thick_slider.valueChanged.connect(self._on_thick_change)
        thick_row.addWidget(self.thick_slider)
        self.thick_value = QLabel(f"{self.config.get('line_thick', 6)}px")
        self.thick_value.setStyleSheet("color: #00e676; font-weight: bold;")
        self.thick_value.setMinimumWidth(40)
        thick_row.addWidget(self.thick_value)
        thick_row.addStretch()
        layout.addLayout(thick_row)

        # Max length
        len_row = QHBoxLayout()
        len_label = QLabel("Max Length")
        len_label.setMinimumWidth(80)
        len_row.addWidget(len_label)
        self.len_slider = QSlider(Qt.Horizontal)
        self.len_slider.setRange(100, 600)
        self.len_slider.setValue(self.config.get("line_max_len", 300))
        
        self.len_slider.valueChanged.connect(self._on_len_change)
        len_row.addWidget(self.len_slider)
        self.len_value = QLabel(f"{self.config.get('line_max_len', 300)}px")
        self.len_value.setStyleSheet("color: #00e676; font-weight: bold;")
        self.len_value.setMinimumWidth(40)
        len_row.addWidget(self.len_value)
        len_row.addStretch()
        layout.addLayout(len_row)

        # Opacity
        opacity_row = QHBoxLayout()
        opacity_label = QLabel("Brightness")
        opacity_label.setMinimumWidth(80)
        opacity_row.addWidget(opacity_label)
        self.line_opacity_slider = QSlider(Qt.Horizontal)
        self.line_opacity_slider.setRange(50, 255)
        self.line_opacity_slider.setValue(self.config.get("line_alpha", 200))
        
        self.line_opacity_slider.valueChanged.connect(self._on_line_opacity_change)
        opacity_row.addWidget(self.line_opacity_slider)
        self.line_opacity_value = QLabel(f"{int(self.config.get('line_alpha', 200) / 255 * 100)}%")
        self.line_opacity_value.setStyleSheet("color: #00e676; font-weight: bold;")
        self.line_opacity_value.setMinimumWidth(40)
        opacity_row.addWidget(self.line_opacity_value)
        opacity_row.addStretch()
        layout.addLayout(opacity_row)

        layout.addSpacing(6)
        default_btn = QPushButton("Reset to Default")
        default_btn.setCursor(Qt.PointingHandCursor)
        default_btn.setMaximumWidth(150)
        default_btn.setStyleSheet("""
            QPushButton {
                background-color: #1c1c30; color: #9090a8;
                border: 1px solid #2c2c48; padding: 8px 16px;
                border-radius: 6px; font-size: 12px;
            }
            QPushButton:hover { border-color: #00e676; color: #e0e0f0; }
        """)
        default_btn.clicked.connect(self._reset_indicator)
        layout.addWidget(default_btn)

        # Color
        layout.addSpacing(24)

        color_heading = QLabel("Color")
        color_heading.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(color_heading)

        color_desc = QLabel("Choose the color for sound indicators")
        color_desc.setStyleSheet("color: #6a6a84; font-size: 12px;")
        layout.addWidget(color_desc)

        layout.addSpacing(8)

        # Color preview + custom picker
        color_row = QHBoxLayout()

        # Color swatches - includes colorblind-friendly options
        presets = [
            [0, 255, 140],      # Green
            [0, 220, 255],      # Cyan
            [255, 70, 50],      # Red
            [255, 220, 0],      # Yellow (colorblind-friendly)
            [255, 180, 50],     # Orange
            [180, 60, 255],     # Purple
            [255, 255, 255],    # White (works for all)
        ]

        c = self.config["color"]
        self._color_btns = []
        for rgb in presets:
            btn = QPushButton()
            btn.setFixedSize(42, 42)
            btn.setCursor(Qt.PointingHandCursor)
            is_active = (c == rgb)
            border = "#ffffff" if is_active else "transparent"
            bw = "3px" if is_active else "2px"
            btn.setStyleSheet(
                f"QPushButton {{ background-color: rgb({rgb[0]},{rgb[1]},{rgb[2]}); "
                f"border-radius: 6px; border: {bw} solid {border}; }}"
                f"QPushButton:hover {{ border: 3px solid #ffffff; }}"
            )
            btn.clicked.connect(lambda checked, r=rgb: self._set_color(r))
            self._color_btns.append((btn, rgb))
            color_row.addWidget(btn)
            color_row.addSpacing(8)

        # Custom picker button
        color_row.addSpacing(8)
        self.color_btn = QPushButton("Custom")
        self.color_btn.setCursor(Qt.PointingHandCursor)
        self.color_btn.setStyleSheet(
            "QPushButton { background-color: #1c1c30; border-radius: 6px; "
            "border: 1px solid #2c2c48; color: #c0c0d4; padding: 10px 18px; font-size: 12px; }"
            "QPushButton:hover { border-color: #00e676; color: #00e676; }"
        )
        self.color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self.color_btn)

        color_row.addStretch()
        layout.addLayout(color_row)

        layout.addStretch()
        return tab

    def _reset_indicator(self):
        self.thick_slider.setValue(14)
        self.len_slider.setValue(300)
        self.line_opacity_slider.setValue(200)

    def _on_thick_change(self, val):
        self.thick_value.setText(f"{val}px")
        self.config["line_thick"] = val
        save_config(self.config)

    def _on_len_change(self, val):
        self.len_value.setText(f"{val}px")
        self.config["line_max_len"] = val
        save_config(self.config)

    def _on_line_opacity_change(self, val):
        self.line_opacity_value.setText(f"{int(val / 255 * 100)}%")
        self.config["line_alpha"] = val
        save_config(self.config)

    def _calibrate_speakers(self):
        from .calibration import CalibrationDialog
        dialog = CalibrationDialog(self.config, self)
        dialog.exec_()


    def _pick_color(self):
        c = self.config["color"]
        color = QColorDialog.getColor(QColor(*c), self, "Pick Radar Color")
        if color.isValid():
            self._set_color([color.red(), color.green(), color.blue()])

    def _set_color(self, rgb):
        self.config["color"] = rgb
        save_config(self.config)
        self.settings_changed.emit()
        # Update swatch highlights
        if hasattr(self, '_color_btns'):
            for btn, btn_rgb in self._color_btns:
                is_active = (btn_rgb == rgb)
                border = "#ffffff" if is_active else "transparent"
                bw = "3px" if is_active else "2px"
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: rgb({btn_rgb[0]},{btn_rgb[1]},{btn_rgb[2]}); "
                    f"border-radius: 6px; border: {bw} solid {border}; }}"
                    f"QPushButton:hover {{ border: 3px solid #ffffff; }}"
                )

    def _build_sounds_tab(self):
        """Agent ability editor - manage sound signatures."""
        from . import fingerprints as fp

        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        heading = QLabel("Sound Signatures - Valorant")
        heading.setObjectName("heading")
        layout.addWidget(heading)

        desc = QLabel(
            "Each agent ability has a unique sound fingerprint.\n"
            "The radar uses these to identify what sound is playing."
        )
        desc.setStyleSheet("color: #a0a0b8; font-size: 12px;")
        layout.addWidget(desc)

        # Two-panel layout: agents left, abilities right
        panels = QHBoxLayout()

        # Agent list
        agent_panel = QVBoxLayout()
        agent_label = QLabel("Agents:")
        agent_label.setStyleSheet("color: #a0a0b8; font-size: 12px;")
        agent_panel.addWidget(agent_label)

        self.agent_list = QListWidget()
        self.agent_list.setMaximumWidth(150)
        for name in fp.get_agent_list():
            role = fp.VALORANT_AGENTS[name].get("role", "")
            item = QListWidgetItem(f"{name}")
            item.setData(Qt.UserRole, name)
            item.setToolTip(role)
            self.agent_list.addItem(item)
        self.agent_list.currentItemChanged.connect(self._on_agent_select)
        agent_panel.addWidget(self.agent_list)

        # Add common sounds entry
        common_item = QListWidgetItem("-- Common Sounds --")
        common_item.setData(Qt.UserRole, "__common__")
        self.agent_list.insertItem(0, common_item)

        panels.addLayout(agent_panel)

        # Ability list + signature display
        ability_panel = QVBoxLayout()
        ability_label = QLabel("Sounds:")
        ability_label.setStyleSheet("color: #a0a0b8; font-size: 12px;")
        ability_panel.addWidget(ability_label)

        self.ability_list = QListWidget()
        self.ability_list.currentItemChanged.connect(self._on_ability_select)
        ability_panel.addWidget(self.ability_list)

        # Signature visualization
        self.sig_display = QLabel("Select an agent and sound to view its signature.")
        self.sig_display.setStyleSheet("color: #a0a0b8; font-size: 12px;")
        self.sig_display.setWordWrap(True)
        ability_panel.addWidget(self.sig_display)

        panels.addLayout(ability_panel)
        layout.addLayout(panels)

        # Info
        info = QLabel(
            "These signatures are pre-built from Valorant audio analysis.\n"
            "Community can update them when Valorant patches change sounds."
        )
        info.setStyleSheet("color: #505068; font-size: 9px;")
        layout.addWidget(info)

        return tab

    def _on_agent_select(self, current, previous):
        from . import fingerprints as fp
        self.ability_list.clear()
        if current is None:
            return

        agent_name = current.data(Qt.UserRole)

        if agent_name == "__common__":
            for sig in fp.VALORANT_COMMON:
                icon = sig.get("icon", "")
                item = QListWidgetItem(f"{sig['name']}  ({sig.get('type', '')})")
                item.setData(Qt.UserRole, sig)
                self.ability_list.addItem(item)
        else:
            abilities = fp.get_agent_abilities(agent_name)
            for ab in abilities:
                item = QListWidgetItem(f"[{ab['key']}] {ab['name']}  ({ab['icon']})")
                item.setData(Qt.UserRole, ab)
                self.ability_list.addItem(item)

    def _on_ability_select(self, current, previous):
        if current is None:
            self.sig_display.setText("")
            return

        sig = current.data(Qt.UserRole)
        if not sig:
            return

        ratios = sig.get("band_ratios", [0, 0, 0, 0, 0])
        bands = ["Sub (20-150Hz)", "Low (150-500Hz)", "Mid (500-2kHz)",
                 "High (2-6kHz)", "Ultra (6-16kHz)"]

        lines = [f"<b>{sig.get('name', '?')}</b>  -  icon: {sig.get('icon', '?')}",
                 f"transient: {'yes' if sig.get('transient') else 'no'}", ""]

        for i, (band, ratio) in enumerate(zip(bands, ratios)):
            bar_len = int(ratio * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            lines.append(f"<code>{band:18s} {bar} {ratio*100:.0f}%</code>")

        self.sig_display.setText("<br>".join(lines))

    def _build_performance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        heading = QLabel("Performance")
        heading.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(heading)

        desc = QLabel("Balance between visual quality and game FPS.\nLower = more FPS for your game.")
        desc.setStyleSheet("color: #a0a0b8;")
        layout.addWidget(desc)

        # --- Overlay FPS ---
        layout.addSpacing(10)
        fps_label = QLabel("Overlay Render Rate")
        fps_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(fps_label)

        fps_row = QHBoxLayout()
        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setMinimum(15)
        self.fps_slider.setMaximum(120)
        current_fps = max(15, min(120, int(1000 / self.config.get("render_interval", 33))))
        self.fps_slider.setValue(current_fps)
        self.fps_value = QLabel(f"{current_fps} FPS")
        self.fps_value.setMinimumWidth(60)
        self.fps_slider.valueChanged.connect(self._on_fps_changed)
        fps_row.addWidget(self.fps_slider)
        fps_row.addWidget(self.fps_value)
        layout.addLayout(fps_row)

        fps_hint = QLabel("Lower = more game FPS. 30 recommended. 15 = maximum savings.")
        fps_hint.setStyleSheet("color: #6a6a84; font-size: 12px;")
        layout.addWidget(fps_hint)

        # --- Analysis Rate ---
        layout.addSpacing(10)
        analyze_label = QLabel("Audio Analysis Rate")
        analyze_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(analyze_label)

        analyze_row = QHBoxLayout()
        self.analyze_slider = QSlider(Qt.Horizontal)
        self.analyze_slider.setMinimum(1)
        self.analyze_slider.setMaximum(4)
        # Map: 1=Low(64), 2=Medium(32), 3=High(16), 4=Ultra(8)
        analyze_map = {64: 1, 32: 2, 16: 3, 8: 4}
        current_analyze = analyze_map.get(self.config.get("analyze_every", 32), 2)
        self.analyze_slider.setValue(current_analyze)
        self.analyze_value = QLabel(["", "Low", "Medium", "High", "Ultra"][current_analyze])
        self.analyze_value.setMinimumWidth(60)
        self.analyze_slider.valueChanged.connect(self._on_analyze_changed)
        analyze_row.addWidget(self.analyze_slider)
        analyze_row.addWidget(self.analyze_value)
        layout.addLayout(analyze_row)

        analyze_hint = QLabel("Low = most FPS savings. High = faster detection. Medium recommended.")
        analyze_hint.setStyleSheet("color: #6a6a84; font-size: 12px;")
        layout.addWidget(analyze_hint)

        # --- Detection Sensitivity ---
        layout.addSpacing(10)
        sens_label = QLabel("Detection Sensitivity")
        sens_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(sens_label)

        sens_row = QHBoxLayout()
        self.sens_slider = QSlider(Qt.Horizontal)
        self.sens_slider.setMinimum(1)
        self.sens_slider.setMaximum(10)
        # threshold 0.001-0.010 mapped to 1-10 (inverted: 10=most sensitive)
        current_thresh = self.config.get("dir_threshold", 0.002)
        sens_val = max(1, min(10, int(11 - current_thresh * 1000)))
        self.sens_slider.setValue(sens_val)
        self.sens_value = QLabel(f"{sens_val}/10")
        self.sens_value.setMinimumWidth(60)
        self.sens_slider.valueChanged.connect(self._on_sens_changed)
        sens_row.addWidget(self.sens_slider)
        sens_row.addWidget(self.sens_value)
        layout.addLayout(sens_row)

        sens_hint = QLabel("Higher = catches quieter footsteps but may show false positives.")
        sens_hint.setStyleSheet("color: #6a6a84; font-size: 12px;")
        layout.addWidget(sens_hint)

        # --- Presets ---
        layout.addSpacing(15)
        preset_label = QLabel("Quick Presets")
        preset_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(preset_label)

        preset_row = QHBoxLayout()

        self._preset_btns = {}
        for name, key in [("Max FPS", "max_fps"), ("Balanced", "balanced"), ("Best Quality", "quality"), ("Custom", "custom")]:
            btn = QPushButton(name)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, k=key: self._apply_perf_preset(k))
            self._preset_btns[key] = btn
            preset_row.addWidget(btn)

        preset_row.addStretch()
        layout.addLayout(preset_row)

        self.perf_status = QLabel("")
        layout.addWidget(self.perf_status)

        # Highlight the current preset
        self._update_preset_highlight()

        layout.addStretch()
        return tab

    def _on_fps_changed(self, value):
        self.fps_value.setText(f"{value} FPS")
        interval = max(8, int(1000 / value))
        self.config["render_interval"] = interval
        save_config(self.config)
        if self.overlay:
            self.overlay.render_timer.setInterval(interval)
        self._update_preset_highlight()

    def _on_analyze_changed(self, value):
        labels = ["", "Low", "Medium", "High", "Ultra"]
        values = [0, 64, 32, 16, 8]
        self.analyze_value.setText(labels[value])
        self.config["analyze_every"] = values[value]
        save_config(self.config)
        self._update_preset_highlight()

    def _on_sens_changed(self, value):
        self.sens_value.setText(f"{value}/10")
        threshold = (11 - value) * 0.001
        self.config["dir_threshold"] = threshold
        save_config(self.config)
        self._update_preset_highlight()

    def _get_current_preset(self):
        """Check which preset matches current settings."""
        fps = self.fps_slider.value()
        analyze = self.analyze_slider.value()
        sens = self.sens_slider.value()
        if fps == 15 and analyze == 1 and sens == 7:
            return "max_fps"
        elif fps == 30 and analyze == 2 and sens == 7:
            return "balanced"
        elif fps == 60 and analyze == 3 and sens == 8:
            return "quality"
        return "custom"

    def _update_preset_highlight(self):
        """Highlight the active preset button."""
        current = self._get_current_preset()
        for key, btn in self._preset_btns.items():
            if key == current:
                btn.setStyleSheet(
                    "QPushButton { background-color: #00c853; color: #0a0a14; "
                    "border: none; border-radius: 6px; padding: 9px 20px; "
                    "font-size: 12px; font-weight: bold; }"
                    "QPushButton:hover { background-color: #00e676; }"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton { background-color: #1c1c30; color: #c0c0d4; "
                    "border: 1px solid #2c2c48; border-radius: 6px; padding: 9px 20px; "
                    "font-size: 12px; }"
                    "QPushButton:hover { border-color: #00e676; color: #00e676; }"
                )

    def _apply_perf_preset(self, preset):
        if preset == "max_fps":
            self.fps_slider.setValue(15)
            self.analyze_slider.setValue(1)
            self.sens_slider.setValue(7)
            self.perf_status.setText("Max FPS applied")
        elif preset == "balanced":
            self.fps_slider.setValue(30)
            self.analyze_slider.setValue(2)
            self.sens_slider.setValue(7)
            self.perf_status.setText("Balanced applied")
        elif preset == "quality":
            self.fps_slider.setValue(60)
            self.analyze_slider.setValue(3)
            self.sens_slider.setValue(8)
            self.perf_status.setText("Best Quality applied")
        elif preset == "custom":
            self.perf_status.setText("Custom settings active")
        self._update_preset_highlight()

    def _build_profiles_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        heading = QLabel("Profiles")
        heading.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(heading)

        desc = QLabel(
            "Each game has its own profiles. Your local profiles are private.\n"
            "Community profiles can be imported and shared."
        )
        desc.setStyleSheet("color: #9090a8; font-size: 12px;")
        layout.addWidget(desc)

        # Two-panel layout: games left, profiles right
        panels = QHBoxLayout()
        panels.setSpacing(12)

        # Game list (left)
        game_panel = QVBoxLayout()
        game_label = QLabel("Games")
        game_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        game_label.setStyleSheet("color: #9090a8;")
        game_panel.addWidget(game_label)

        self.game_list = QListWidget()
        self.game_list.setMinimumWidth(200)
        self.game_list.setMaximumWidth(220)
        self.game_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.game_list.currentItemChanged.connect(self._on_game_select)
        game_panel.addWidget(self.game_list)

        fav_game_btn = QPushButton("Favorite")
        fav_game_btn.clicked.connect(self._toggle_fav_game)
        game_panel.addWidget(fav_game_btn)

        panels.addLayout(game_panel)

        # Right side: sub-tabs for My Profiles / Community
        right_panel = QVBoxLayout()

        self.profile_tabs = QTabWidget()

        # My Profiles tab
        my_tab = QWidget()
        my_layout = QVBoxLayout(my_tab)
        my_layout.setContentsMargins(8, 8, 8, 8)

        self.profile_list = QTreeWidget()
        self.profile_list.setHeaderLabels(["Name", "Status", "Updated"])
        self.profile_list.setRootIsDecorated(False)
        self.profile_list.setAlternatingRowColors(False)
        self.profile_list.header().setStretchLastSection(True)
        self.profile_list.setColumnWidth(0, 200)
        self.profile_list.setColumnWidth(1, 80)
        my_layout.addWidget(self.profile_list)

        my_btn_row = QHBoxLayout()
        my_btn_row.setSpacing(6)

        new_btn = QPushButton("+ New")
        new_btn.setObjectName("primary")
        new_btn.setMaximumWidth(80)
        new_btn.clicked.connect(self._new_profile)
        my_btn_row.addWidget(new_btn)

        activate_btn = QPushButton("Activate")
        activate_btn.setMaximumWidth(80)
        activate_btn.clicked.connect(self._activate_profile)
        my_btn_row.addWidget(activate_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setMaximumWidth(60)
        edit_btn.clicked.connect(self._edit_profile)
        my_btn_row.addWidget(edit_btn)

        fav_btn = QPushButton("Fav")
        fav_btn.setMaximumWidth(50)
        fav_btn.clicked.connect(self._toggle_fav_profile)
        my_btn_row.addWidget(fav_btn)

        share_btn = QPushButton("Share")
        share_btn.setMaximumWidth(60)
        share_btn.clicked.connect(self._share_profile)
        my_btn_row.addWidget(share_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setMaximumWidth(60)
        delete_btn.clicked.connect(self._delete_profile)
        my_btn_row.addWidget(delete_btn)

        my_layout.addLayout(my_btn_row)

        self.profile_tabs.addTab(my_tab, "My Profiles")

        # Community tab
        community_tab = QWidget()
        community_layout = QVBoxLayout(community_tab)
        community_layout.setContentsMargins(8, 8, 8, 8)
        community_layout.setSpacing(6)

        # Search bar
        search_row = QHBoxLayout()
        self.comm_search = QLineEdit()
        self.comm_search.setPlaceholderText("Search profiles...")
        self.comm_search.setStyleSheet("padding: 8px; border-radius: 6px;")
        self.comm_search.textChanged.connect(self._filter_community)
        search_row.addWidget(self.comm_search)

        # Sort dropdown
        self.comm_sort = QComboBox()
        self.comm_sort.addItems(["Newest", "Most Liked", "Name A-Z"])
        self.comm_sort.setMaximumWidth(120)
        self.comm_sort.currentIndexChanged.connect(self._sort_community)
        search_row.addWidget(self.comm_sort)

        community_layout.addLayout(search_row)

        # Community profile list with columns
        self.community_list = QTreeWidget()
        self.community_list.setHeaderLabels(["Name", "Rating", "Updated"])
        self.community_list.setRootIsDecorated(False)
        self.community_list.setAlternatingRowColors(False)
        self.community_list.header().setStretchLastSection(True)
        self.community_list.setColumnWidth(0, 200)
        self.community_list.setColumnWidth(1, 80)
        community_layout.addWidget(self.community_list)

        # Buttons
        comm_btn_row = QHBoxLayout()
        comm_btn_row.setSpacing(6)

        import_btn = QPushButton("Import")
        import_btn.setMaximumWidth(70)
        import_btn.clicked.connect(self._import_profile)
        comm_btn_row.addWidget(import_btn)

        copy_btn = QPushButton("Copy")
        copy_btn.setObjectName("primary")
        copy_btn.setMaximumWidth(60)
        copy_btn.clicked.connect(self._copy_community_profile)
        comm_btn_row.addWidget(copy_btn)

        self.like_btn = QPushButton("Like")
        self.like_btn.setMaximumWidth(55)
        self.like_btn.setStyleSheet("QPushButton { color: #00e676; }")
        self.like_btn.clicked.connect(self._like_profile)
        comm_btn_row.addWidget(self.like_btn)

        self.dislike_btn = QPushButton("Dislike")
        self.dislike_btn.setMaximumWidth(65)
        self.dislike_btn.setStyleSheet("QPushButton { color: #ff5252; }")
        self.dislike_btn.clicked.connect(self._dislike_profile)
        comm_btn_row.addWidget(self.dislike_btn)

        comm_btn_row.addStretch()
        community_layout.addLayout(comm_btn_row)

        self.profile_tabs.addTab(community_tab, "Community")

        right_panel.addWidget(self.profile_tabs)

        self.profile_info = QLabel("")
        self.profile_info.setStyleSheet("font-size: 12px;")
        right_panel.addWidget(self.profile_info)

        panels.addLayout(right_panel)
        layout.addLayout(panels)

        # Populate games from existing profiles
        self._refresh_game_list()

        return tab

    def _refresh_game_list(self):
        """Build the game list from available profiles."""
        self.game_list.clear()
        games = set()

        for filename, data in prof.list_profiles():
            game = data.get("game", "Any Game")
            games.add(game)

        # Popular games - always show these
        default_games = [
            "Any Game",
            "Valorant",
            "Counter-Strike 2",
            "Apex Legends",
            "Overwatch 2",
            "Fortnite",
            "Call of Duty: Warzone",
            "Rainbow Six Siege",
            "PUBG",
            "Escape from Tarkov",
            "Hunt: Showdown",
            "Deadlock",
            "Marvel Rivals",
            "The Finals",
            "XDefiant",
            "Battlefield 2042",
        ]
        for g in default_games:
            games.add(g)

        favs = self._get_favorites()
        fav_games = favs.get("games", [])

        # Sort: favorites first, then alphabetical
        sorted_games = sorted(games, key=lambda g: (0 if g in fav_games else 1, g))

        for game in sorted_games:
            item = QListWidgetItem(game)
            item.setData(Qt.UserRole, game)
            if game in fav_games:
                item.setIcon(self._create_star_icon(True))
            self.game_list.addItem(item)

        # Select the active profile's game
        active_profile_name = self.config.get("active_profile", "default")
        try:
            active_data = prof.load_profile(active_profile_name)
            active_game = active_data.get("game", "Any Game")
        except Exception:
            active_game = "Any Game"

        for i in range(self.game_list.count()):
            if self.game_list.item(i).data(Qt.UserRole) == active_game:
                self.game_list.setCurrentRow(i)
                break

    def _toggle_fav_game(self):
        """Toggle favorite on the selected game."""
        item = self.game_list.currentItem()
        if not item:
            return
        game = item.data(Qt.UserRole)
        favs = self._get_favorites()
        if game in favs["games"]:
            favs["games"].remove(game)
        else:
            favs["games"].append(game)
        self._save_favorites(favs)
        self._refresh_game_list()

    def _toggle_fav_profile(self):
        """Toggle favorite on the selected profile."""
        item = self.profile_list.currentItem()
        if not item:
            return
        filename = item.data(0, Qt.UserRole)
        favs = self._get_favorites()
        if filename in favs["profiles"]:
            favs["profiles"].remove(filename)
        else:
            favs["profiles"].append(filename)
        self._save_favorites(favs)
        current_game = self.game_list.currentItem()
        game = current_game.data(Qt.UserRole) if current_game else None
        self._refresh_profiles(game)

    def _on_game_select(self, current, previous):
        """Show profiles for the selected game, split into local and community."""
        if current is None:
            return
        game = current.data(Qt.UserRole)
        self._refresh_profiles(game)

    def _refresh_profiles(self, game_filter=None):
        self.profile_list.clear()
        self.community_list.clear()
        active = self.config.get("active_profile", "default")
        favs = self._get_favorites()
        fav_profiles = favs.get("profiles", [])

        for filename, data in prof.list_profiles():
            game = data.get("game", "Any Game")

            if game_filter and game != game_filter:
                continue

            name = data.get("name", filename)
            author = data.get("author", "")

            # Default game profiles always go to My Profiles
            # User's own profiles (no author) go to My Profiles
            # Community shared (has author) go to Community
            is_default = prof.is_default_profile(filename)
            is_community = not is_default and author != "" and author != "SoundSight"

            updated = data.get("updated", data.get("created", ""))

            if is_community:
                # Community columns: Name | Likes | Date
                likes = data.get("likes", 0)
                dislikes = data.get("dislikes", 0)
                score = likes - dislikes
                if score > 0:
                    like_text = f"+{score}"
                elif score < 0:
                    like_text = f"{score}"
                else:
                    like_text = "0" if (likes + dislikes) > 0 else ""

                item = QTreeWidgetItem([name, like_text, updated])

                # Color the rating: green for positive, red for negative
                if score > 0:
                    item.setForeground(1, QColor(0, 230, 118))
                elif score < 0:
                    item.setForeground(1, QColor(255, 82, 82))

                # Add thumbs icon
                if likes + dislikes > 0:
                    icon = self._create_thumb_icon(score)
                    item.setIcon(1, icon)
                item.setData(0, Qt.UserRole, filename)
                item.setData(0, Qt.UserRole + 1, data)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignRight)
                self.community_list.addTopLevelItem(item)
            else:
                # My Profiles columns: Name | Status | Date
                status = "Active" if filename == active else ""
                item = QTreeWidgetItem([name, status, updated])
                item.setData(0, Qt.UserRole, filename)
                item.setTextAlignment(1, Qt.AlignCenter)
                item.setTextAlignment(2, Qt.AlignRight)

                if filename in fav_profiles:
                    item.setIcon(0, self._create_star_icon(True))

                self.profile_list.addTopLevelItem(item)
                if filename == active:
                    self.profile_list.setCurrentItem(item)

    def _get_favorites(self):
        """Get set of favorited items (games and profiles)."""
        import os, json
        fav_path = os.path.join(prof.PROFILES_DIR, ".favorites.json")
        try:
            if os.path.exists(fav_path):
                with open(fav_path, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"games": [], "profiles": []}

    def _save_favorites(self, favs):
        import os, json
        fav_path = os.path.join(prof.PROFILES_DIR, ".favorites.json")
        with open(fav_path, "w") as f:
            json.dump(favs, f, indent=2)

    def _create_star_icon(self, filled=True):
        """Create a star icon for favorites."""
        size = 16
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)

        color = QColor(255, 200, 50) if filled else QColor(80, 80, 100)

        # Star shape
        import math
        path = QPainterPath()
        cx, cy = size / 2, size / 2
        outer = size * 0.45
        inner = size * 0.2
        for i in range(5):
            angle_out = math.radians(-90 + i * 72)
            angle_in = math.radians(-90 + i * 72 + 36)
            ox = cx + math.cos(angle_out) * outer
            oy = cy + math.sin(angle_out) * outer
            ix = cx + math.cos(angle_in) * inner
            iy = cy + math.sin(angle_in) * inner
            if i == 0:
                path.moveTo(ox, oy)
            else:
                path.lineTo(ox, oy)
            path.lineTo(ix, iy)
        path.closeSubpath()

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(color))
        p.drawPath(path)
        p.end()
        return QIcon(pm)

    def _create_thumb_icon(self, score):
        """Create a thumbs up (green) or thumbs down (red) icon."""
        size = 16
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)

        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)

        if score >= 0:
            # Thumbs up - green
            color = QColor(0, 230, 118)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(color))
            # Thumb shape pointing up
            path = QPainterPath()
            path.moveTo(4, 10)
            path.lineTo(4, 6)
            path.lineTo(6, 3)
            path.lineTo(8, 1)
            path.lineTo(9, 3)
            path.lineTo(9, 6)
            path.lineTo(13, 6)
            path.lineTo(14, 7)
            path.lineTo(13, 11)
            path.lineTo(12, 13)
            path.lineTo(6, 13)
            path.lineTo(4, 12)
            path.closeSubpath()
            p.drawPath(path)
            # Cuff
            p.drawRect(1, 10, 3, 4)
        else:
            # Thumbs down - red
            color = QColor(255, 82, 82)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(color))
            # Thumb shape pointing down
            path = QPainterPath()
            path.moveTo(4, 5)
            path.lineTo(4, 9)
            path.lineTo(6, 12)
            path.lineTo(8, 14)
            path.lineTo(9, 12)
            path.lineTo(9, 9)
            path.lineTo(13, 9)
            path.lineTo(14, 8)
            path.lineTo(13, 4)
            path.lineTo(12, 2)
            path.lineTo(6, 2)
            path.lineTo(4, 3)
            path.closeSubpath()
            p.drawPath(path)
            # Cuff
            p.drawRect(1, 1, 3, 4)

        p.end()
        return QIcon(pm)

    def _filter_community(self, text):
        """Filter community list by search text."""
        for i in range(self.community_list.topLevelItemCount()):
            item = self.community_list.topLevelItem(i)
            item.setHidden(text.lower() not in item.text(0).lower())

    def _sort_community(self, index):
        """Sort community list."""
        current_game = self.game_list.currentItem()
        if current_game:
            self._refresh_profiles(current_game.data(Qt.UserRole))

    def _get_user_votes(self):
        """Get dict of user's votes: {filename: 'like' or 'dislike'}"""
        import os, json
        votes_path = os.path.join(prof.PROFILES_DIR, ".votes.json")
        try:
            if os.path.exists(votes_path):
                with open(votes_path, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_user_votes(self, votes):
        import os, json
        votes_path = os.path.join(prof.PROFILES_DIR, ".votes.json")
        with open(votes_path, "w") as f:
            json.dump(votes, f, indent=2)

    def _like_profile(self):
        """Like a community profile. If already liked, undo. If disliked, switch."""
        item = self.community_list.currentItem()
        if not item:
            return
        filename = item.data(0, Qt.UserRole)
        try:
            data = prof.load_profile(filename)
            votes = self._get_user_votes()
            current_vote = votes.get(filename, None)

            if current_vote == "like":
                # Already liked, undo
                data["likes"] = data.get("likes", 0) - 1
                del votes[filename]
            else:
                if current_vote == "dislike":
                    # Was dislike, remove dislike first
                    data["dislikes"] = max(0, data.get("dislikes", 0) - 1)
                # Add like
                data["likes"] = data.get("likes", 0) + 1
                votes[filename] = "like"

            prof.save_profile(filename, data)
            self._save_user_votes(votes)
            current_game = self.game_list.currentItem()
            game = current_game.data(Qt.UserRole) if current_game else None
            self._refresh_profiles(game)
        except Exception:
            pass

    def _dislike_profile(self):
        """Dislike a community profile. If already disliked, undo. If liked, switch."""
        item = self.community_list.currentItem()
        if not item:
            return
        filename = item.data(0, Qt.UserRole)
        try:
            data = prof.load_profile(filename)
            votes = self._get_user_votes()
            current_vote = votes.get(filename, None)

            if current_vote == "dislike":
                # Already disliked, undo
                data["dislikes"] = max(0, data.get("dislikes", 0) - 1)
                del votes[filename]
            else:
                if current_vote == "like":
                    # Was like, remove like first
                    data["likes"] = max(0, data.get("likes", 0) - 1)
                # Add dislike
                data["dislikes"] = data.get("dislikes", 0) + 1
                votes[filename] = "dislike"

            prof.save_profile(filename, data)
            self._save_user_votes(votes)
            current_game = self.game_list.currentItem()
            game = current_game.data(Qt.UserRole) if current_game else None
            self._refresh_profiles(game)
        except Exception:
            pass

    def _copy_community_profile(self):
        """Copy a community profile to local profiles."""
        item = self.community_list.currentItem()
        if not item:
            return
        filename = item.data(0, Qt.UserRole)
        try:
            data = prof.load_profile(filename)
            # Make it local by clearing author
            data["author"] = ""
            data["name"] = data.get("name", filename)
            new_name = prof._sanitize_name(data["name"])
            prof.save_profile(new_name, data)
            current_game = self.game_list.currentItem()
            game = current_game.data(Qt.UserRole) if current_game else None
            self._refresh_profiles(game)
            self.profile_info.setText(f"Copied to My Profiles")
            self.profile_info.setStyleSheet("color: #00e676;")
        except Exception as e:
            self.profile_info.setText(f"Error: {e}")
            self.profile_info.setStyleSheet("color: #ff4444;")

    def _new_profile(self):
        """Create a new profile for the selected game. Only asks for name."""
        current_game = self.game_list.currentItem()
        if not current_game:
            return
        game = current_game.data(Qt.UserRole)

        # Ask for profile name only
        name, ok = QInputDialog.getText(self, "New Profile", "Profile name:")
        if not ok or not name.strip():
            return

        name = name.strip()

        # Create profile
        new_data = prof.DEFAULT_PROFILE.copy()
        new_data["sound_focus"] = prof.DEFAULT_PROFILE["sound_focus"].copy()
        import datetime
        new_data["name"] = name
        new_data["game"] = game
        new_data["author"] = ""
        new_data["created"] = datetime.date.today().isoformat()
        new_data["updated"] = datetime.date.today().isoformat()

        # Find unique filename
        import os
        base = prof._sanitize_name(f"{game}_{name}")
        filename = base
        counter = 1
        while os.path.exists(os.path.join(prof.PROFILES_DIR, f"{filename}.json")):
            filename = f"{base}_{counter}"
            counter += 1

        prof.save_profile(filename, new_data)
        self._refresh_profiles(game)
        self.profile_info.setText(f"Created: {name}")
        self.profile_info.setStyleSheet("color: #00e676;")

    def _share_profile(self):
        """Share profile to Community. Copies it with your name as author."""
        item = self.profile_list.currentItem()
        if not item:
            return
        filename = item.data(0, Qt.UserRole)
        try:
            data = prof.load_profile(filename)

            # Can't share default profiles
            if prof.is_default_profile(filename):
                self.profile_info.setText("Cannot share a default profile. Create your own first.")
                self.profile_info.setStyleSheet("color: #ff4444;")
                return

            # Copy to community
            import os, datetime
            shared_data = data.copy()
            shared_data["author"] = data.get("name", "User")
            shared_data["updated"] = datetime.date.today().isoformat()

            # Save as a new community profile
            base = prof._sanitize_name(f"shared_{data.get('game', 'game')}_{data.get('name', 'profile')}")
            shared_filename = base
            counter = 1
            while os.path.exists(os.path.join(prof.PROFILES_DIR, f"{shared_filename}.json")):
                shared_filename = f"{base}_{counter}"
                counter += 1

            prof.save_profile(shared_filename, shared_data)

            # Refresh
            current_game = self.game_list.currentItem()
            game = current_game.data(Qt.UserRole) if current_game else None
            self._refresh_profiles(game)
            self.profile_info.setText(f"Shared to Community!")
            self.profile_info.setStyleSheet("color: #00e676;")
        except Exception as e:
            self.profile_info.setText(f"Error: {e}")
            self.profile_info.setStyleSheet("color: #ff4444;")

    def _edit_profile(self):
        """Open profile editor dialog."""
        item = self.profile_list.currentItem()
        if not item:
            return
        filename = item.data(0, Qt.UserRole)
        from .profile_editor import ProfileEditor
        editor = ProfileEditor(filename, self.config, self)
        if editor.exec_() == editor.Accepted:
            # Refresh lists
            self._refresh_game_list()
            self.profile_info.setText("Profile saved")
            self.profile_info.setStyleSheet("color: #00e676;")
            self.settings_changed.emit()

    def _activate_profile(self):
        item = self.profile_list.currentItem()
        if not item:
            return
        filename = item.data(0, Qt.UserRole)
        try:
            profile_data = prof.load_profile(filename)
            prof.apply_profile_to_config(self.config, profile_data)
            self.config["active_profile"] = filename
            save_config(self.config)
            # Refresh with current game filter
            current_game = self.game_list.currentItem()
            game = current_game.data(Qt.UserRole) if current_game else None
            self._refresh_profiles(game)
            self.profile_info.setText(f"Activated: {profile_data.get('name', filename)}")
            self.profile_info.setStyleSheet("color: #00e676;")
            self.settings_changed.emit()
        except Exception as e:
            self.profile_info.setText(f"Error: {e}")
            self.profile_info.setStyleSheet("color: #ff4444;")

    def _import_profile(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Profile", "", "JSON Files (*.json)"
        )
        if path:
            try:
                filename = prof.import_profile(path)
                self._refresh_game_list()
                self.profile_info.setText(f"Imported: {filename}")
                self.profile_info.setStyleSheet("color: #00e676;")
            except Exception as e:
                self.profile_info.setText(f"Error: {e}")
                self.profile_info.setStyleSheet("color: #ff4444;")

    def _export_profile(self):
        item = self.profile_list.currentItem()
        if not item:
            return
        filename = item.data(0, Qt.UserRole)
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Profile", f"{filename}.json", "JSON Files (*.json)"
        )
        if path:
            try:
                prof.export_profile(filename, path)
                self.profile_info.setText(f"Exported: {path}")
                self.profile_info.setStyleSheet("color: #00e676;")
            except Exception as e:
                self.profile_info.setText(f"Error: {e}")
                self.profile_info.setStyleSheet("color: #ff4444;")

    def _delete_profile(self):
        item = self.profile_list.currentItem()
        if not item:
            return
        filename = item.data(0, Qt.UserRole)
        try:
            prof.delete_profile(filename)
            current_game = self.game_list.currentItem()
            game = current_game.data(Qt.UserRole) if current_game else None
            self._refresh_profiles(game)
            self.profile_info.setText(f"Deleted: {filename}")
            self.profile_info.setStyleSheet("color: #9090a8;")
        except ValueError as e:
            self.profile_info.setText(str(e))
            self.profile_info.setStyleSheet("color: #ff4444;")

    def _build_about_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(6)
        layout.setContentsMargins(20, 24, 20, 20)

        CARD = """
            QFrame {
                background-color: #16162a;
                border: 1px solid #22223c;
                border-radius: 8px;
            }
        """

        # App info
        title = QLabel("SoundSight")
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setStyleSheet("color: #00e676;")
        layout.addWidget(title)

        from .updater import VERSION
        subtitle = QLabel(f"v{VERSION}  |  Visual Sound Radar for Hearing Accessibility")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #8080a0;")
        layout.addWidget(subtitle)

        desc = QLabel(
            "Visual overlay that shows game sounds as screen indicators.\n"
            "For gamers with hearing loss, single-sided deafness, or anyone\n"
            "who needs visual sound cues."
        )
        desc.setFont(QFont("Segoe UI", 12))
        desc.setStyleSheet("color: #6a6a84;")
        layout.addWidget(desc)

        layout.addSpacing(16)

        # Keyboard Shortcuts card
        shortcuts_heading = QLabel("Keyboard Shortcuts")
        shortcuts_heading.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(shortcuts_heading)

        layout.addSpacing(4)

        sc_card = QFrame()
        sc_card.setStyleSheet(CARD)
        sc_card.setSizePolicy(sc_card.sizePolicy().horizontalPolicy(), sc_card.sizePolicy().verticalPolicy())
        from PyQt5.QtWidgets import QSizePolicy
        sc_card.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sc_layout = QVBoxLayout(sc_card)
        sc_layout.setContentsMargins(16, 12, 16, 12)
        sc_layout.setSpacing(6)

        shortcuts = [
            ("F10", "Show / Hide overlay"),
        ]
        for key, action in shortcuts:
            row = QHBoxLayout()
            k = QLabel(key)
            k.setFont(QFont("Segoe UI", 12, QFont.Bold))
            k.setStyleSheet("color: #00e676; border: none; min-width: 60px;")
            a = QLabel(action)
            a.setFont(QFont("Segoe UI", 12))
            a.setStyleSheet("color: #c0c0d4; border: none;")
            row.addWidget(k)
            row.addWidget(a)
            row.addStretch()
            sc_layout.addLayout(row)

        layout.addWidget(sc_card)

        layout.addSpacing(20)

        # Actions
        actions_heading = QLabel("Actions")
        actions_heading.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(actions_heading)

        layout.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        update_btn = QPushButton("Updates")
        update_btn.setCursor(Qt.PointingHandCursor)
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #00c853; color: #0a0a14; border: none;
                font-weight: bold; padding: 9px 18px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #00e676; }
        """)
        update_btn.clicked.connect(self._check_updates)
        btn_row.addWidget(update_btn)

        self.autostart_btn = QPushButton()
        self.autostart_btn.setCursor(Qt.PointingHandCursor)
        self._update_autostart_btn()
        self.autostart_btn.clicked.connect(self._toggle_autostart)
        btn_row.addWidget(self.autostart_btn)

        restart_btn = QPushButton("Restart")
        restart_btn.setCursor(Qt.PointingHandCursor)
        restart_btn.clicked.connect(self._restart_app)
        btn_row.addWidget(restart_btn)

        rerun_btn = QPushButton("Setup Wizard")
        rerun_btn.setCursor(Qt.PointingHandCursor)
        rerun_btn.clicked.connect(self._rerun_wizard)
        btn_row.addWidget(rerun_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.update_status = QLabel("")
        layout.addWidget(self.update_status)

        layout.addSpacing(16)

        # Supported games
        games_heading = QLabel("Supported Games")
        games_heading.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(games_heading)

        tested = QLabel("Tested:  Valorant (7.1)  |  CS2 (Stereo)")
        tested.setFont(QFont("Segoe UI", 12))
        tested.setStyleSheet("color: #00e676;")
        layout.addWidget(tested)

        untested = QLabel(
            "Should work with any game that outputs audio.\n"
            "Auto-detects surround or stereo automatically."
        )
        untested.setWordWrap(True)
        untested.setFont(QFont("Segoe UI", 12))
        untested.setStyleSheet("color: #6a6a84;")
        layout.addWidget(untested)

        layout.addStretch()
        return tab

    def _restart_app(self):
        """Restart the application."""
        import sys, subprocess
        from PyQt5.QtWidgets import QApplication
        subprocess.Popen([sys.executable, "-m", "sound_radar"] + sys.argv[1:])
        QApplication.quit()

    def _check_updates(self):
        from .updater import VERSION, GITHUB_REPO
        if not GITHUB_REPO:
            self.update_status.setText(f"v{VERSION} - Updates available after GitHub publish")
            self.update_status.setStyleSheet("color: #8080a0;")
        else:
            self.update_status.setText("Checking...")
            self.update_status.setStyleSheet("color: #8080a0;")
            from .updater import check_for_updates_async, show_update_notification
            def _on_result(has_update, version, url):
                if has_update:
                    self.update_status.setText(f"New version available: v{version}")
                    self.update_status.setStyleSheet("color: #00e676; font-weight: bold;")
                    show_update_notification(self, version, url)
                else:
                    self.update_status.setText(f"v{VERSION} - You're up to date")
                    self.update_status.setStyleSheet("color: #00e676;")
            check_for_updates_async(_on_result)

    def _rerun_wizard(self):
        self.config["first_run"] = True
        save_config(self.config)
        from .error_handler import show_info
        show_info("Setup Wizard", "Restart SoundSight to run the Setup Wizard again.")

    def _is_autostart_enabled(self):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, "SoundSight")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False

    def _toggle_autostart(self):
        import sys, os
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            if self._is_autostart_enabled():
                winreg.DeleteValue(key, "SoundSight")
            else:
                if getattr(sys, 'frozen', False):
                    exe_path = f'"{sys.executable}"'
                else:
                    # Get the project directory for working directory
                    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    exe_path = f'cmd /c "cd /d "{project_dir}" && "{sys.executable}" -m sound_radar"'
                winreg.SetValueEx(key, "SoundSight", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
        except Exception as e:
            from .error_handler import show_error
            show_error("Auto-start Error", f"Could not change auto-start setting:\n{e}")
        self._update_autostart_btn()

    def _update_autostart_btn(self):
        if self._is_autostart_enabled():
            self.autostart_btn.setText("Auto-start: On")
        else:
            self.autostart_btn.setText("Auto-start: Off")
