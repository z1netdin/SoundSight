"""Auto-updater - checks GitHub for new versions.

Checks on startup (once per day max). If a new version exists,
shows a notification. User clicks to download.

No forced updates. No background downloads. Simple and transparent.
"""

import os
import json
import time
import threading
from .config import get_app_dir

VERSION = "1.0.0"
GITHUB_REPO = "z1netdin/SoundSight"
CHECK_INTERVAL = 86400  # Check once per day (seconds)
UPDATE_CACHE = os.path.join(get_app_dir(), ".update_check")


def get_current_version():
    return VERSION


def _load_last_check():
    """Load when we last checked for updates."""
    try:
        if os.path.exists(UPDATE_CACHE):
            with open(UPDATE_CACHE, "r") as f:
                data = json.load(f)
                return data.get("last_check", 0), data.get("latest_version", VERSION)
    except Exception:
        pass
    return 0, VERSION


def _save_last_check(latest_version):
    """Save the last check time and result."""
    try:
        with open(UPDATE_CACHE, "w") as f:
            json.dump({
                "last_check": time.time(),
                "latest_version": latest_version,
            }, f)
    except Exception:
        pass


def check_for_updates_async(callback=None):
    """Check GitHub for new releases in a background thread.

    callback(has_update, latest_version, download_url) is called on completion.
    """
    if not GITHUB_REPO:
        return  # No repo configured yet

    # Don't check too often
    last_check, cached_version = _load_last_check()
    if time.time() - last_check < CHECK_INTERVAL:
        if cached_version != VERSION and callback:
            callback(True, cached_version, f"https://github.com/{GITHUB_REPO}/releases/latest")
        return

    def _check():
        try:
            import urllib.request
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "SoundRadar"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())

            latest = data.get("tag_name", "").lstrip("v")
            download_url = data.get("html_url", "")

            _save_last_check(latest)

            if latest and latest != VERSION:
                if callback:
                    callback(True, latest, download_url)
            else:
                if callback:
                    callback(False, VERSION, "")

        except Exception:
            # Network error, no internet, etc. - silently skip
            _save_last_check(VERSION)

    thread = threading.Thread(target=_check, daemon=True)
    thread.start()


def show_update_notification(parent, latest_version, download_url):
    """Show a non-blocking update notification."""
    from PyQt5.QtWidgets import QMessageBox, QPushButton
    import webbrowser

    msg = QMessageBox(parent)
    msg.setWindowTitle("SoundSight Update")
    msg.setText(f"A new version is available: v{latest_version}\n\n"
                f"You have: v{VERSION}")
    msg.setInformativeText("Download the latest version from GitHub?")

    download_btn = msg.addButton("Download", QMessageBox.AcceptRole)
    msg.addButton("Later", QMessageBox.RejectRole)

    msg.exec_()

    if msg.clickedButton() == download_btn:
        webbrowser.open(download_url)
