# SoundSight

**Visual Sound Radar for Hearing Accessibility**

I play FPS games competitively and I'm deaf. I built SoundSight for my own need and decided to share it with everyone for free.

SoundSight shows game sounds as visual indicators on your screen edges. Footsteps, gunshots, abilities - a bar appears on the side where the sound comes from. Closer sounds show a bigger bar.

## Tested Games

- **Valorant** - 7.1 surround (full 360 direction)
- **CS2** - Stereo (left/right detection)
- Should work with any game that outputs audio

## How It Works

```
Game Audio -> WASAPI Loopback Capture -> Directional Analysis -> Screen Overlay
```

- Captures the same audio your headset receives
- Subtracts your own sounds (footsteps, shots) so only enemy sounds show
- Auto-detects 7.1 surround or stereo
- Thin bar on screen edge grows bigger when enemy is closer

## Setup

```
pip install -r requirements.txt
python -m sound_radar
```

The Setup Wizard guides you through first-time setup.

### For Best Accuracy (7.1 Surround)

1. Install [Voicemeeter Banana](https://vb-audio.com/Voicemeeter/banana.htm) (free)
2. Set Voicemeeter Input as Windows default output
3. Set Voicemeeter Input to 7.1 Surround, 48000 Hz in properties
4. Launch SoundSight

### Controls

| Key | Action |
|-----|--------|
| **F10** | Show / Hide overlay |

## Features

- **Setup Wizard** - guides first-time setup step by step
- **Settings Panel** - audio device, appearance, performance tuning
- **Speaker Calibration** - adjust speaker positions visually (7.1)
- **Performance Presets** - Max FPS, Balanced, Best Quality
- **Auto-start** - launch with Windows
- **Low CPU** - optimized to not affect game FPS
- **Customizable** - thickness, length, brightness, color

## Requirements

- Windows 10/11
- Python 3.10+
- Any headset (7.1 virtual surround recommended)

## Dependencies

```
PyAudioWPatch    - WASAPI loopback audio capture
numpy            - Audio processing
scipy            - Signal analysis
PyQt5            - Overlay and settings UI
keyboard         - Global hotkeys
pycaw            - Volume control
```

## Who Is This For

- Deaf gamers
- Hard of hearing gamers
- Single-sided deafness
- Anyone who needs visual sound cues

## License

Free for personal and educational use.
Commercial use prohibited without permission.
Contact for commercial licensing.
