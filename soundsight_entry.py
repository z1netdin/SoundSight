"""Entry point for PyInstaller build."""
import sys
import os

# Add the parent directory to path so sound_radar package is found
if getattr(sys, 'frozen', False):
    base = sys._MEIPASS
else:
    base = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base)

from sound_radar.main import main
main()
