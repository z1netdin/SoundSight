"""Profile Editor - edit what sounds to focus on.

Users can toggle sound types on/off and adjust settings per profile.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QSlider, QLineEdit, QGroupBox, QFrame, QComboBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from .config import save_config
from . import profiles as prof


class ProfileEditor(QDialog):
    """Edit a profile - toggle sounds, adjust sensitivity, change color."""

    def __init__(self, profile_filename, config, parent=None):
        super().__init__(parent)
        self.profile_filename = profile_filename
        self.config = config
        self.profile_data = prof.load_profile(profile_filename)
        self.is_default = prof.is_default_profile(profile_filename)

        self.setWindowTitle(f"Edit Profile - {self.profile_data.get('name', '')}")
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        self.setMinimumSize(500, 550)
        self.setMaximumSize(650, 700)

        self._build_ui()

    def showEvent(self, event):
        super().showEvent(event)
        from .theme import apply_dark_titlebar
        apply_dark_titlebar(self)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # Profile name
        if self.is_default:
            # Default profiles: show name as label, can't change
            title = QLabel(f"{self.profile_data.get('game', '')} - Default Profile")
            title.setFont(QFont("Segoe UI", 14, QFont.Bold))
            layout.addWidget(title)
            self.name_edit = None
            self.game_edit = None
        else:
            # User profiles: editable name
            name_row = QHBoxLayout()
            name_label = QLabel("Profile Name:")
            name_label.setFont(QFont("Segoe UI", 11))
            name_row.addWidget(name_label)

            self.name_edit = QLineEdit(self.profile_data.get("name", ""))
            self.name_edit.setStyleSheet("padding: 8px; border-radius: 6px;")
            name_row.addWidget(self.name_edit)
            layout.addLayout(name_row)

            # Game selector
            game_row = QHBoxLayout()
            game_label = QLabel("Game:")
            game_label.setFont(QFont("Segoe UI", 11))
            game_row.addWidget(game_label)

            self.game_edit = QComboBox()
            self.game_edit.setEditable(True)
            self.game_edit.addItems([
                "Any Game", "Valorant", "Counter-Strike 2", "Apex Legends",
                "Overwatch 2", "Fortnite", "Call of Duty: Warzone",
                "Rainbow Six Siege", "PUBG", "Escape from Tarkov",
                "Hunt: Showdown", "Deadlock", "Marvel Rivals",
                "The Finals", "XDefiant", "Battlefield 2042",
            ])
            current_game = self.profile_data.get("game", "Any Game")
            idx = self.game_edit.findText(current_game)
            if idx >= 0:
                self.game_edit.setCurrentIndex(idx)
            else:
                self.game_edit.setEditText(current_game)
            game_row.addWidget(self.game_edit)
            layout.addLayout(game_row)

        layout.addSpacing(8)

        # Sound Focus - what to detect
        focus_group = QGroupBox("Sound Focus - what to show on the overlay")
        focus_layout = QVBoxLayout(focus_group)
        focus_layout.setSpacing(6)

        focus_desc = QLabel("Turn on the sounds you want to detect.\nTurn off sounds you want to ignore.")
        focus_desc.setStyleSheet("color: #9090a8; font-size: 10px; border: none;")
        focus_layout.addWidget(focus_desc)

        focus_layout.addSpacing(4)

        # Self-sound filter option
        self.self_filter_check = QCheckBox("Filter my own sounds")
        self.self_filter_check.setChecked(self.profile_data.get("filter_self", True))
        self.self_filter_check.setFont(QFont("Segoe UI", 11))
        self.self_filter_check.setStyleSheet("""
            QCheckBox { spacing: 8px; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px;
                border: 2px solid #28283e; background: #1c1c32; }
            QCheckBox::indicator:checked { background: #00e676; border-color: #00e676; }
        """)
        focus_layout.addWidget(self.self_filter_check)

        filter_desc = QLabel("ON = hide your own footsteps/shots (use with headset)\nOFF = show everything (use without headset)")
        filter_desc.setStyleSheet("color: #606078; font-size: 9px; border: none;")
        focus_layout.addWidget(filter_desc)

        focus_layout.addSpacing(8)

        # Get current focus settings from profile
        focus = self.profile_data.get("sound_focus", {})

        self.focus_checks = {}
        sounds = [
            ("footsteps", "Footsteps", "Walking, running, jumping, landing", True),
            ("gunshots", "Gunshots", "All weapon fire", True),
            ("abilities", "Abilities", "Agent/character abilities", True),
            ("spike", "Spike / Objective", "Plant, defuse, capture", True),
            ("reload", "Reload", "Weapon reload sounds", False),
            ("weapon_drop", "Weapon Drop / Pickup", "Dropping or picking up weapons", False),
            ("movement", "Other Movement", "Rope, teleporter, zipline", True),
        ]

        for key, name, desc, default_on in sounds:
            row = QHBoxLayout()
            cb = QCheckBox(name)
            cb.setChecked(focus.get(key, default_on))
            cb.setFont(QFont("Segoe UI", 11))
            cb.setStyleSheet("""
                QCheckBox {
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: 2px solid #28283e;
                    background: #1c1c32;
                }
                QCheckBox::indicator:checked {
                    background: #00e676;
                    border-color: #00e676;
                }
            """)
            row.addWidget(cb)

            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #606078; font-size: 10px;")
            row.addWidget(desc_label)
            row.addStretch()

            focus_layout.addLayout(row)
            self.focus_checks[key] = cb

        layout.addWidget(focus_group)

        layout.addSpacing(8)

        # Sensitivity override
        sens_group = QGroupBox("Sensitivity for this profile")
        sens_layout = QVBoxLayout(sens_group)

        self.sens_slider = QSlider(Qt.Horizontal)
        self.sens_slider.setRange(1, 100)
        current_sens = self.profile_data.get("sensitivity", 0.008)
        self.sens_slider.setValue(max(1, min(100, int((0.055 - current_sens) / 0.05 * 100))))
        self.sens_label = QLabel("")
        self._update_sens_label()
        self.sens_slider.valueChanged.connect(self._update_sens_label)
        sens_layout.addWidget(self.sens_label)
        sens_layout.addWidget(self.sens_slider)

        layout.addWidget(sens_group)

        layout.addStretch()

        # Save / Cancel buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Profile")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _update_sens_label(self):
        val = self.sens_slider.value()
        sens = 0.055 - (val / 100 * 0.05)
        if sens <= 0.008:
            text = "Maximum - detects very quiet sounds"
        elif sens <= 0.015:
            text = "High - recommended for competitive"
        elif sens <= 0.03:
            text = "Medium - balanced"
        else:
            text = "Low - only loud sounds"
        self.sens_label.setText(text)
        self.sens_label.setStyleSheet("color: #9090a8; font-size: 11px; border: none;")

    def _save(self):
        # Update profile data (name and game locked for defaults)
        if self.name_edit is not None:
            self.profile_data["name"] = self.name_edit.text().strip() or "Unnamed"
        if self.game_edit is not None:
            self.profile_data["game"] = self.game_edit.currentText().strip() or "Any Game"

        # Save sound focus
        focus = {}
        for key, cb in self.focus_checks.items():
            focus[key] = cb.isChecked()
        self.profile_data["sound_focus"] = focus
        self.profile_data["filter_self"] = self.self_filter_check.isChecked()

        # Save sensitivity
        val = self.sens_slider.value()
        self.profile_data["sensitivity"] = 0.055 - (val / 100 * 0.05)

        # Update date
        import datetime
        self.profile_data["updated"] = datetime.date.today().isoformat()

        # Write to disk
        prof.save_profile(self.profile_filename, self.profile_data)

        self.accept()
