@echo off
echo Building SoundSight EXE...
echo.
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "SoundSight" --add-data "profiles;profiles" sound_radar/__main__.py
echo.
echo Build complete! Check the dist\SoundSight folder.
pause
