"""SoundSight - Main entry point.

First launch: shows Setup Wizard.
After setup: starts overlay with saved settings.

Usage:
    python -m sound_radar              (normal - wizard or radar)
    python -m sound_radar --list       (list audio devices)
    python -m sound_radar --device N   (use specific device)
"""

import sys
import threading
import argparse
import numpy as np

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from .config import load_config, save_config
from .audio_capture import AudioCapture
from .audio_analyzer import AudioAnalyzer
from .radar_overlay import RadarOverlay
from .error_handler import (
    DeviceNotFoundError, WASAPINotAvailableError, AudioStreamError,
    ErrorRecoveryDialog, show_error,
)
from . import profiles as prof


def list_devices():
    """List all audio devices (power user CLI tool)."""
    import pyaudiowpatch as pyaudio
    pa = pyaudio.PyAudio()
    print("\n  Available Audio Devices:")
    print("  " + "-" * 60)
    for i in range(pa.get_device_count()):
        dev = pa.get_device_info_by_index(i)
        if dev.get("isLoopbackDevice", False):
            ch = dev["maxInputChannels"]
            rate = int(dev["defaultSampleRate"])
            name = dev["name"]
            print(f"  [{i:2d}] {name}")
            print(f"       {ch}ch | {rate} Hz <<< LOOPBACK")
    pa.terminate()
    print()


def audio_processing_loop(capture, analyzer, overlay, config=None):
    """Sliding window audio processing - optimized for low CPU.

    Collects multiple small blocks before analyzing to reduce
    processing overhead while keeping low latency.
    """
    WINDOW_SIZE = 1024
    ANALYZE_EVERY = (config or {}).get("analyze_every", 32)  # User configurable from Performance tab
    channels = capture.channels

    # Pre-allocated buffer - no allocations in the hot loop
    window = np.zeros((WINDOW_SIZE, channels), dtype=np.float32)
    write_pos = 0
    block_count = 0

    print(f"[Audio] Processing started - optimized for low CPU")

    while capture._running:
        frame = capture.get_frame(timeout=0.02)
        if frame is None:
            continue

        # Write directly into pre-allocated buffer (circular)
        n = len(frame)
        if write_pos + n <= WINDOW_SIZE:
            window[write_pos:write_pos + n] = frame
        else:
            split = WINDOW_SIZE - write_pos
            window[write_pos:] = frame[:split]
            window[:n - split] = frame[split:]
        write_pos = (write_pos + n) % WINDOW_SIZE

        block_count += 1
        if block_count % ANALYZE_EVERY != 0:
            continue

        # Roll buffer so it's in order (cheap numpy op)
        ordered = np.roll(window, -write_pos, axis=0)
        result = analyzer.analyze(ordered)
        if result is not None:
            overlay.add_event(result)


def start_radar(config, app):
    """Initialize and start the radar. Returns True on success."""

    # Load active profile
    profile_signatures = []
    try:
        profile = prof.load_profile(config.get("active_profile", "default"))
        prof.apply_profile_to_config(config, profile)
        profile_signatures = profile.get("sound_signatures", [])
    except Exception:
        pass  # Use defaults if profile fails

    # If no profile signatures, load default Valorant signatures
    if not profile_signatures:
        from .fingerprints import get_all_valorant_signatures
        profile_signatures = get_all_valorant_signatures()

    # Audio capture
    capture = AudioCapture(
        device_index=config.get("audio_device"),
        block_size=8,
    )

    try:
        capture.start()
    except (DeviceNotFoundError, WASAPINotAvailableError) as e:
        dialog = ErrorRecoveryDialog(
            "Audio Device Error",
            str(e),
            show_setup=True,
        )
        action = dialog.get_action()
        if action == ErrorRecoveryDialog.SETUP:
            config["first_run"] = True
            save_config(config)
            return start_with_wizard(config, app)
        elif action == ErrorRecoveryDialog.RETRY:
            return start_radar(config, app)
        else:
            return False
    except Exception as e:
        dialog = ErrorRecoveryDialog(
            "Audio Error",
            f"Could not start audio capture:\n{e}",
            show_setup=True,
        )
        action = dialog.get_action()
        if action == ErrorRecoveryDialog.SETUP:
            config["first_run"] = True
            save_config(config)
            return start_with_wizard(config, app)
        elif action == ErrorRecoveryDialog.RETRY:
            return start_radar(config, app)
        else:
            return False

    ch = capture.channels
    if ch >= 8:
        print(f"[Audio] 7.1 Surround - full 360° radar")
    elif ch >= 6:
        print(f"[Audio] 5.1 Surround")
    else:
        print(f"[Audio] Stereo")

    # Load calibrated angles if saved
    if "channel_angles" in config:
        from .audio_analyzer import CHANNEL_ANGLES_71
        for ch_str, angle in config["channel_angles"].items():
            CHANNEL_ANGLES_71[int(ch_str)] = angle

    # Analyzer
    analyzer = AudioAnalyzer(
        sample_rate=capture.sample_rate,
        channels=capture.channels,
        sensitivity=config["sensitivity"],
        audio_mode=config.get("audio_mode", "auto"),
    )
    analyzer.load_signatures(profile_signatures)

    # Load sound focus from profile
    try:
        profile = prof.load_profile(config.get("active_profile", "default"))
        analyzer.load_sound_focus(
            profile.get("sound_focus", {}),
            filter_self=profile.get("filter_self", True)
        )
    except Exception:
        pass

    # Overlay
    overlay = RadarOverlay(config)
    overlay.show()

    # Tray icon
    from .tray_icon import TrayIcon
    from .settings_panel import SettingsPanel
    tray = TrayIcon(overlay, config, SettingsPanel)
    tray.show()

    # Open settings window on start so the user can see the app
    settings = SettingsPanel(config, overlay)
    settings.show()

    # Hotkeys - keyboard module needs admin on some systems
    try:
        import keyboard
        keyboard.add_hotkey("F10", overlay.toggle_visibility)
        print(f"[Hotkeys] F10 = Show/Hide")
    except ImportError:
        print(f"[Warning] 'keyboard' module not installed - hotkeys disabled")
    except Exception as e:
        print(f"[Warning] Hotkeys need admin rights: {e}")
        print(f"[Warning] Run as Administrator for F10 hotkey")

    print(f"\n[Radar] Running!")
    print(f"  F10 = Show/Hide")

    # Check for updates (background, non-blocking)
    from .updater import check_for_updates_async, show_update_notification
    def _on_update(has_update, version, url):
        if has_update:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(3000, lambda: show_update_notification(None, version, url))
    check_for_updates_async(_on_update)

    # Audio thread
    audio_thread = threading.Thread(
        target=audio_processing_loop,
        args=(capture, analyzer, overlay, config),
        daemon=True,
    )
    audio_thread.start()

    # Run Qt event loop
    try:
        exit_code = app.exec_()
    finally:
        capture.stop()

    return True


def start_with_wizard(config, app):
    """Show setup wizard, then start radar."""
    from .setup_wizard import SetupWizard

    wizard = SetupWizard(config)
    result = wizard.exec_()

    if result == SetupWizard.Rejected:
        return False

    # Reload config (wizard saved it)
    config.update(load_config())
    return start_radar(config, app)


def main():
    parser = argparse.ArgumentParser(description="SoundSight")
    parser.add_argument("--list", action="store_true", help="List audio devices")
    parser.add_argument("--device", type=int, default=None, help="Audio device index")
    parser.add_argument("--setup", action="store_true", help="Force setup wizard")
    args = parser.parse_args()

    if args.list:
        list_devices()
        return

    # Tell Windows this is SoundSight, not python.exe
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("soundsight.app")
        # Try to rename the process for volume mixer
        try:
            import setproctitle
            setproctitle.setproctitle("SoundSight")
        except ImportError:
            pass
    except Exception:
        pass

    # Set process to BELOW NORMAL priority - game gets CPU first
    try:
        import ctypes
        BELOW_NORMAL = 0x00004000
        ctypes.windll.kernel32.SetPriorityClass(
            ctypes.windll.kernel32.GetCurrentProcess(), BELOW_NORMAL)
    except Exception:
        pass

    # Force dark title bar on all windows (Windows 10/11)
    try:
        import ctypes
        ctypes.windll.dwmapi.DwmSetWindowAttribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
        # Will apply to each window via theme helper
    except Exception:
        pass

    # Qt app
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("SoundSight")

    # Better font rendering
    from PyQt5.QtGui import QFont
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.PreferNoHinting)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    # App icon - shows in taskbar, window titles, alt-tab
    import os
    from PyQt5.QtGui import QIcon
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Apply premium dark theme to ALL windows
    from .theme import APP_STYLESHEET
    app.setStyleSheet(APP_STYLESHEET)

    config = load_config()

    # CLI device override
    if args.device is not None:
        config["audio_device"] = args.device
        config["first_run"] = False

    # Force wizard
    if args.setup:
        config["first_run"] = True

    # First run → wizard, otherwise → start directly
    try:
        if config.get("first_run", True):
            success = start_with_wizard(config, app)
        else:
            success = start_radar(config, app)
    except Exception as e:
        show_error("Unexpected Error", f"SoundSight encountered an error:\n\n{e}")
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
