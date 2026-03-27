"""Configuration for SoundSight.

Handles settings persistence and path resolution.
Works in both development (python -m sound_radar) and frozen (EXE) mode.
"""

import json
import os
import sys


def get_app_dir():
    """Get the application directory - works in dev and EXE mode."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DEFAULT_CONFIG = {
    # First run
    "first_run": True,

    # Active profile
    "active_profile": "default",

    # Radar UI
    "radar_size": 180,
    "radar_opacity": 0.15,
    "radar_x": 100,
    "radar_y": 100,
    "visual_mode": "edge_glow",  # edge_glow, pulse_flash, screen_tint

    # Audio
    "audio_device": None,
    "sensitivity": 0.008,
    "filter_self": False,  # default: show all sounds like hearing players hear

    # Appearance
    "color": [0, 255, 140],
}

CONFIG_PATH = os.path.join(get_app_dir(), "config.json")


def load_config():
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config.update(json.load(f))
        except (json.JSONDecodeError, IOError):
            pass
    return config


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
