"""Profile system for SoundSight.

Profiles let users save game-specific settings and sound configurations.
Community can create and share profiles for different games.

Profile structure:
{
    "name": "Valorant Competitive",
    "game": "Valorant",
    "version": 1,
    "author": "",
    "description": "Optimized for Valorant competitive play",
    "color": [0, 255, 140],
    "sensitivity": 0.015,
    "radar_opacity": 0.15,
    "radar_size": 180,
    "sound_signatures": {},   # Future: frequency fingerprints per sound type
    "icon_mappings": {}       # Future: custom icons per sound type
}
"""

import json
import os
import shutil
from .config import get_app_dir


PROFILES_DIR = os.path.join(get_app_dir(), "profiles")

import datetime

DEFAULT_PROFILE = {
    "name": "Default",
    "game": "Any Game",
    "version": 1,
    "author": "SoundSight",
    "description": "Works with any game. Green wave visualization.",
    "created": datetime.date.today().isoformat(),
    "updated": datetime.date.today().isoformat(),
    "likes": 0,
    "color": [0, 255, 140],
    "sensitivity": 0.008,
    "filter_self": False,
    "radar_opacity": 0.15,
    "radar_size": 180,
    "sound_signatures": {},
    "icon_mappings": {},
    "sound_focus": {
        "footsteps": True,
        "gunshots": True,
        "abilities": True,
        "spike": True,
        "reload": False,
        "weapon_drop": False,
        "movement": True,
    },
}

# Default profiles for each game - cannot be deleted
GAME_DEFAULTS = {
    "default": {
        "name": "Default", "game": "Any Game",
    },
    "valorant_default": {
        "name": "Default", "game": "Valorant",
    },
    "cs2_default": {
        "name": "Default", "game": "Counter-Strike 2",
    },
    "apex_default": {
        "name": "Default", "game": "Apex Legends",
    },
    "overwatch2_default": {
        "name": "Default", "game": "Overwatch 2",
    },
    "fortnite_default": {
        "name": "Default", "game": "Fortnite",
    },
    "warzone_default": {
        "name": "Default", "game": "Call of Duty: Warzone",
    },
    "r6siege_default": {
        "name": "Default", "game": "Rainbow Six Siege",
    },
    "pubg_default": {
        "name": "Default", "game": "PUBG",
    },
    "tarkov_default": {
        "name": "Default", "game": "Escape from Tarkov",
    },
    "hunt_default": {
        "name": "Default", "game": "Hunt: Showdown",
    },
    "deadlock_default": {
        "name": "Default", "game": "Deadlock",
    },
    "marvel_rivals_default": {
        "name": "Default", "game": "Marvel Rivals",
    },
    "the_finals_default": {
        "name": "Default", "game": "The Finals",
    },
    "xdefiant_default": {
        "name": "Default", "game": "XDefiant",
    },
    "bf2042_default": {
        "name": "Default", "game": "Battlefield 2042",
    },
}


def _make_game_profile(game_info):
    """Create a default profile for a game."""
    profile = DEFAULT_PROFILE.copy()
    profile["sound_focus"] = DEFAULT_PROFILE["sound_focus"].copy()
    profile.update(game_info)
    profile["author"] = "SoundSight"
    profile["version"] = 1
    return profile


def _ensure_profiles_dir():
    """Create profiles directory and all default game profiles."""
    os.makedirs(PROFILES_DIR, exist_ok=True)

    # Create default profiles for each game if missing
    for filename, game_info in GAME_DEFAULTS.items():
        path = os.path.join(PROFILES_DIR, f"{filename}.json")
        if not os.path.exists(path):
            profile = _make_game_profile(game_info)
            save_profile(filename, profile)


def _sanitize_name(name):
    """Convert profile name to safe filename."""
    safe = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
    return safe.strip().lower().replace(' ', '_') or 'unnamed'


def list_profiles():
    """Return list of (filename_without_ext, profile_data) tuples."""
    _ensure_profiles_dir()
    profiles = []
    for f in sorted(os.listdir(PROFILES_DIR)):
        if f.endswith('.json') and not f.startswith('.'):
            name = f[:-5]
            try:
                data = load_profile(name)
                profiles.append((name, data))
            except (json.JSONDecodeError, IOError):
                pass
    return profiles


def load_profile(name):
    """Load a profile by filename (without .json extension)."""
    _ensure_profiles_dir()
    path = os.path.join(PROFILES_DIR, f"{name}.json")
    if not os.path.exists(path):
        if name == "default":
            save_profile("default", DEFAULT_PROFILE)
            return DEFAULT_PROFILE.copy()
        raise FileNotFoundError(f"Profile '{name}' not found")
    with open(path, "r") as f:
        return json.load(f)


def save_profile(name, data):
    """Save a profile."""
    os.makedirs(PROFILES_DIR, exist_ok=True)
    path = os.path.join(PROFILES_DIR, f"{name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def is_default_profile(name):
    """Check if a profile is a built-in default (cannot be deleted)."""
    return name in GAME_DEFAULTS


def delete_profile(name):
    """Delete a profile. Cannot delete default game profiles."""
    if name in GAME_DEFAULTS:
        raise ValueError("Cannot delete a default profile")
    path = os.path.join(PROFILES_DIR, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)


def export_profile(name, dest_path):
    """Export a profile to a file."""
    src = os.path.join(PROFILES_DIR, f"{name}.json")
    if not os.path.exists(src):
        raise FileNotFoundError(f"Profile '{name}' not found")
    shutil.copy2(src, dest_path)


def import_profile(src_path):
    """Import a profile from a file. Returns the profile name."""
    with open(src_path, "r") as f:
        data = json.load(f)

    name = data.get("name", "Imported")
    filename = _sanitize_name(name)

    # Avoid overwriting existing profiles
    base = filename
    counter = 1
    while os.path.exists(os.path.join(PROFILES_DIR, f"{filename}.json")):
        filename = f"{base}_{counter}"
        counter += 1

    save_profile(filename, data)
    return filename


def apply_profile_to_config(config, profile):
    """Merge profile settings into config. Profile overrides appearance,
    but config keeps machine-specific settings (position, device)."""
    for key in ["color", "sensitivity", "radar_opacity", "radar_size"]:
        if key in profile:
            config[key] = profile[key]
    return config
