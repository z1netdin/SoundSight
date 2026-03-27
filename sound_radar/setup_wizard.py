"""First-time Setup Wizard - guides everything from zero to working.

Flow:
1. Welcome
2. Check if Voicemeeter is installed → if not, help install it
3. After restart (if needed) → continue setup
4. Set Windows output to Voicemeeter
5. Set Voicemeeter 7.1 surround
6. Set Voicemeeter A1 to headset
7. Pick audio device for radar
8. Test
9. Done

Simple language. No jargon. Step by step.
"""

import os
import subprocess
import webbrowser

from PyQt5.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

WIZARD_STYLE = """
    * {
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    QWizard, QWizardPage {
        background-color: #111118;
        color: #e8e8f0;
    }
    QLabel {
        color: #d0d0e4;
        font-size: 14px;
    }
    QLabel#title {
        color: #00e676;
        font-size: 22px;
        font-weight: bold;
    }
    QLabel#subtitle {
        color: #8080a0;
        font-size: 13px;
    }
    QLabel#step {
        color: #00e676;
        font-size: 12px;
        font-weight: bold;
    }
    QLabel#body {
        color: #d0d0e4;
        font-size: 14px;
        line-height: 1.6;
    }
    QLabel#warn {
        color: #ffd740;
        font-size: 13px;
    }
    QLabel#success {
        color: #00e676;
        font-size: 14px;
        font-weight: bold;
    }
    QLabel#error {
        color: #ff6b6b;
        font-size: 13px;
    }
    QPushButton {
        background-color: #1c1c30;
        color: #c8c8d8;
        border: 1px solid #2c2c48;
        padding: 10px 24px;
        border-radius: 6px;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #242440;
        border-color: #00e676;
        color: #e8e8f0;
    }
    QPushButton:pressed {
        background-color: #00c853;
        color: #0a0a14;
    }
    QPushButton#green {
        background-color: #00c853;
        color: #0a0a14;
        border: none;
        font-weight: bold;
        font-size: 14px;
        padding: 12px 30px;
        border-radius: 8px;
        letter-spacing: 0.5px;
    }
    QPushButton#green:hover {
        background-color: #00e676;
    }
    QPushButton#green:pressed {
        background-color: #009940;
    }
    QPushButton#green:disabled {
        background-color: #1c1c30;
        color: #4a4a60;
        border: 1px solid #2c2c48;
    }
    QListWidget {
        background-color: #16162a;
        color: #d0d0e0;
        border: 1px solid #2c2c48;
        border-radius: 6px;
        padding: 5px;
        font-size: 13px;
    }
    QListWidget::item {
        padding: 12px;
        border-radius: 4px;
    }
    QListWidget::item:selected {
        background-color: #222240;
        color: #00e676;
    }
    QListWidget::item:hover {
        background-color: #1c1c34;
    }
    QFrame#divider {
        background-color: #1c1c30;
        max-height: 1px;
    }
"""


def _divider():
    line = QFrame()
    line.setObjectName("divider")
    line.setFrameShape(QFrame.HLine)
    return line


def _label(text, obj_name="body"):
    lbl = QLabel(text)
    lbl.setObjectName(obj_name)
    lbl.setWordWrap(True)
    return lbl


def _check_voicemeeter_installed():
    """Check if Voicemeeter Banana is installed."""
    paths = [
        r"C:\Program Files (x86)\VB\Voicemeeter\voicemeeterpro.exe",
        r"C:\Program Files\VB\Voicemeeter\voicemeeterpro.exe",
    ]
    for p in paths:
        if os.path.exists(p):
            return True

    # Check registry
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        )
        for i in range(winreg.QueryInfoKey(key)[0]):
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                try:
                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    if "voicemeeter" in name.lower():
                        winreg.CloseKey(subkey)
                        winreg.CloseKey(key)
                        return True
                except FileNotFoundError:
                    pass
                winreg.CloseKey(subkey)
            except OSError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass

    return False


def _has_loopback_devices():
    """Check if any loopback audio devices exist."""
    try:
        import pyaudiowpatch as pyaudio
        pa = pyaudio.PyAudio()
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            if dev.get("isLoopbackDevice", False):
                pa.terminate()
                return True
        pa.terminate()
    except Exception:
        pass
    return False


# ============================================================
# Page 1: Welcome
# ============================================================
class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(50, 30, 50, 20)

        # Title
        title = QLabel("SoundSight")
        title.setFont(QFont("Segoe UI", 32, QFont.Bold))
        title.setStyleSheet("color: #00e676; background: transparent;")
        layout.addWidget(title)

        layout.addSpacing(4)

        tag = QLabel("Visual Sound Radar for Hearing Accessibility")
        tag.setFont(QFont("Segoe UI", 14))
        tag.setStyleSheet("color: #9090b0; background: transparent;")
        layout.addWidget(tag)

        layout.addSpacing(20)

        desc = QLabel(
            "Shows where game sounds come from as visual indicators\n"
            "on your screen edges. Footsteps, gunshots, abilities.\n\n"
            "For gamers with hearing loss, single-sided deafness,\n"
            "or anyone who needs visual sound cues."
        )
        desc.setFont(QFont("Segoe UI", 14))
        desc.setStyleSheet("color: #d0d0e4; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(20)

        # Steps
        steps_title = QLabel("Quick setup:")
        steps_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        steps_title.setStyleSheet("color: #e8e8f4; background: transparent;")
        layout.addWidget(steps_title)

        layout.addSpacing(8)

        steps = [
            "Install Voicemeeter Banana (free, if needed)",
            "Configure audio device",
            "Ready to play",
        ]
        for i, step in enumerate(steps, 1):
            step_label = QLabel(f"  {i}.  {step}")
            step_label.setFont(QFont("Segoe UI", 14))
            step_label.setStyleSheet("color: #b0b0c8; background: transparent;")
            layout.addWidget(step_label)

        layout.addStretch()


# ============================================================
# Page 2: Voicemeeter Check / Install
# ============================================================
class VoicemeeterPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        self._ready = False

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(50, 24, 50, 20)

        layout.addWidget(_label("Step 1: Audio Software", "title"))
        layout.addSpacing(5)

        self.status_label = _label("Checking...", "body")
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        self.install_info = _label(
            "SoundSight works best with Voicemeeter Banana (free).\n"
            "It lets us capture 7.1 surround audio for precise direction detection.\n\n"
            "Without it, the radar still works but with less accuracy (stereo only).",
            "body"
        )
        layout.addWidget(self.install_info)

        layout.addSpacing(10)

        # Buttons
        btn_row = QHBoxLayout()

        self.download_btn = QPushButton("Download Voicemeeter Banana")
        self.download_btn.setObjectName("green")
        self.download_btn.clicked.connect(self._download)
        btn_row.addWidget(self.download_btn)

        layout.addLayout(btn_row)

        btn_row2 = QHBoxLayout()

        self.skip_btn = QPushButton("Skip")
        self.skip_btn.clicked.connect(self._skip)
        btn_row2.addWidget(self.skip_btn)

        self.recheck_btn = QPushButton("Check Again")
        self.recheck_btn.clicked.connect(self._recheck)
        btn_row2.addWidget(self.recheck_btn)

        btn_row2.addStretch()
        layout.addLayout(btn_row2)

        layout.addSpacing(10)

        self.restart_label = _label("", "warn")
        layout.addWidget(self.restart_label)

        layout.addStretch()

    def initializePage(self):
        self._check()

    def _check(self):
        if _check_voicemeeter_installed():
            self.status_label.setText("Voicemeeter Banana is installed!")
            self.status_label.setObjectName("success")
            self.status_label.setStyleSheet("color: #00e676; font-size: 14px; font-weight: bold;")
            self.download_btn.setVisible(False)
            self.skip_btn.setVisible(False)
            self.recheck_btn.setVisible(False)
            self.install_info.setText(
                "Great - Voicemeeter is ready.\n"
                "Click Next to continue setup."
            )
            self.restart_label.setText("")
            self._ready = True
        elif _has_loopback_devices():
            # No Voicemeeter but has loopback devices - can work in stereo
            self.status_label.setText("Voicemeeter not found, but audio devices available.")
            self.status_label.setStyleSheet("color: #ffd740; font-size: 13px;")
            self._ready = True
        else:
            self.status_label.setText("Voicemeeter is not installed yet.")
            self.status_label.setStyleSheet("color: #ffd740; font-size: 13px;")
            self._ready = False
        self.completeChanged.emit()

    def _download(self):
        webbrowser.open("https://vb-audio.com/Voicemeeter/banana.htm")
        self.restart_label.setText(
            "After installing Voicemeeter:\n"
            "1. Restart your computer\n"
            "2. Open SoundSight again\n"
            "3. Setup will continue from here\n\n"
            "Or click 'I installed it - check again' if you don't want to restart yet."
        )

    def _skip(self):
        self._ready = True
        self.status_label.setText("Skipped - will use stereo mode.")
        self.status_label.setStyleSheet("color: #a0a0b8; font-size: 13px;")
        self.restart_label.setText("You can install Voicemeeter later for better accuracy.")
        self.completeChanged.emit()

    def _recheck(self):
        self._check()

    def isComplete(self):
        return self._ready


# ============================================================
# Page 3: Audio Setup Guide
# ============================================================
class AudioSetupPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(40, 16, 40, 12)

        layout.addWidget(_label("Audio Setup", "title"))
        layout.addSpacing(4)

        self.has_voicemeeter = False
        self.vm_instructions = _label("", "body")
        self.vm_instructions.setStyleSheet("color: #d0d0e4; font-size: 13px;")
        layout.addWidget(self.vm_instructions)

        layout.addStretch()

    def initializePage(self):
        self.has_voicemeeter = _check_voicemeeter_installed()
        if self.has_voicemeeter:
            self.vm_instructions.setText(
                "Do these 2 things (if you haven't already):\n\n"
                "1. Windows Sound Settings\n"
                "    Set output to Voicemeeter Input\n\n"
                "2. Voicemeeter Input Properties\n"
                "    Advanced: 7.1 Surround, 48000 Hz\n\n"
                "Optional: If you want to hear audio\n"
                "    Voicemeeter Banana: Hardware Out A1\n"
                "    Select your output device"
            )
        else:
            self.vm_instructions.setText(
                "No Voicemeeter detected. Using stereo mode.\n\n"
                "Make sure your headset is set as default\n"
                "output in Windows Sound Settings."
            )
            self._done = True
            self.completeChanged.emit()

    def isComplete(self):
        return True


# ============================================================
# Page 4: Device Picker
# ============================================================
class DevicePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        self.selected_device = None

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(40, 20, 40, 15)

        layout.addWidget(_label("Audio Device", "title"))
        layout.addSpacing(4)

        layout.addWidget(_label(
            "Select the device to capture game audio from.",
            "body"
        ))

        layout.addSpacing(8)

        self.device_list = QListWidget()
        self.device_list.setMinimumHeight(150)
        self.device_list.setStyleSheet("""
            QListWidget {
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px 10px;
            }
        """)
        self.device_list.itemClicked.connect(self._on_select)
        layout.addWidget(self.device_list)

        self.status_label = _label("", "body")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def initializePage(self):
        self._scan()

    def _scan(self):
        self.device_list.clear()
        self.selected_device = None

        try:
            import pyaudiowpatch as pyaudio
            pa = pyaudio.PyAudio()

            best_idx = None
            best_ch = 0

            for i in range(pa.get_device_count()):
                dev = pa.get_device_info_by_index(i)
                if not dev.get("isLoopbackDevice", False):
                    continue

                ch = dev["maxInputChannels"]
                name = dev["name"]
                rate = int(dev["defaultSampleRate"])

                # Shorten device name
                short_name = name.split("(")[0].strip() if "(" in name else name
                if ch >= 8:
                    label = f"{short_name} - 7.1 (Best)"
                elif ch >= 6:
                    label = f"{short_name} - 5.1"
                else:
                    label = f"{short_name} - Stereo"

                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, i)
                item.setData(Qt.UserRole + 1, ch)
                self.device_list.addItem(item)

                if ch > best_ch:
                    best_ch = ch
                    best_idx = self.device_list.count() - 1

            pa.terminate()

            if self.device_list.count() == 0:
                self.status_label.setText(
                    "No audio devices found.\n"
                    "Make sure Voicemeeter is running or your headset is connected."
                )
                self.status_label.setStyleSheet("color: #ff6b6b;")
            elif best_idx is not None:
                self.device_list.setCurrentRow(best_idx)
                self._on_select(self.device_list.item(best_idx))

        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            self.status_label.setStyleSheet("color: #ff6b6b;")

    def _on_select(self, item):
        self.selected_device = item.data(Qt.UserRole)
        ch = item.data(Qt.UserRole + 1)
        if ch >= 8:
            self.status_label.setText("7.1 surround selected")
            self.status_label.setStyleSheet("color: #00e676; font-size: 14px; font-weight: bold;")
        elif ch >= 6:
            self.status_label.setText("5.1 surround selected")
            self.status_label.setStyleSheet("color: #00e676; font-size: 14px;")
        else:
            self.status_label.setText("Stereo selected")
            self.status_label.setStyleSheet("color: #ffd740; font-size: 14px;")
        self.completeChanged.emit()

    def isComplete(self):
        return self.selected_device is not None


# ============================================================
# Page 5: Done
# ============================================================
class DonePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(50, 24, 50, 20)

        layout.addWidget(_label("Ready!", "title"))
        layout.addSpacing(8)

        layout.addWidget(_label(
            "SoundSight will show sound direction as a bar\n"
            "on the edge of your screen.\n\n"
            "Bigger bar = closer sound.\n"
            "Smaller bar = farther sound.",
            "body"
        ))

        layout.addSpacing(12)

        layout.addWidget(_label("F10  -  Show / Hide overlay", "step"))

        layout.addStretch()


# ============================================================
# Wizard
# ============================================================
class SetupWizard(QWizard):
    """First-time setup wizard."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("SoundSight")
        self.setMinimumSize(500, 350)
        self.resize(550, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWizardStyle(QWizard.ModernStyle)
        self.setOption(QWizard.NoBackButtonOnStartPage, True)
        self.setStyleSheet(WIZARD_STYLE)
        font = QFont("Segoe UI", 10)
        font.setStyleStrategy(QFont.PreferAntialias)
        self.setFont(font)

        self.welcome = WelcomePage()
        self.voicemeeter = VoicemeeterPage()
        self.audio_setup = AudioSetupPage()
        self.device = DevicePage()
        self.done = DonePage()

        self.addPage(self.welcome)
        self.addPage(self.voicemeeter)
        self.addPage(self.audio_setup)
        self.addPage(self.device)
        self.addPage(self.done)

        self.setButtonText(QWizard.NextButton, "Next")
        self.setButtonText(QWizard.BackButton, "Back")
        self.setButtonText(QWizard.FinishButton, "Start SoundSight")

    def showEvent(self, event):
        super().showEvent(event)
        from .theme import apply_dark_titlebar
        apply_dark_titlebar(self)

    def accept(self):
        """Save settings when wizard finishes."""
        if self.device.selected_device is not None:
            self.config["audio_device"] = self.device.selected_device
        self.config["first_run"] = False

        from .config import save_config
        save_config(self.config)

        super().accept()
