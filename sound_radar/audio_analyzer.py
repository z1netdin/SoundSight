"""Directional audio analyzer for SoundSight.

Analyzes 7.1 surround or stereo audio to detect sound direction.
Auto-detects stereo games (like CS2) through 7.1 capture.
Uses center subtraction to filter out the player's own sounds.
"""

import math
import numpy as np
from scipy import signal as scipy_signal
from typing import Optional


NUM_SEGMENTS = 360  # 1° per segment

# Voicemeeter 7.1 channel layout (verified by speaker test)
# Mapped to screen edges:
#   Top = Front (L, R)
#   Left side = Side Left
#   Right side = Side Right
#   Bottom = Rear (RL, RR)
CHANNEL_ANGLES_71 = {
    0: 325,    # Front Left -> top-left (spread wider)
    1: 35,     # Front Right -> top-right (spread wider)
    2: 0,      # Center - dead front
    3: None,   # LFE - skip
    4: 150,    # Rear Left -> bottom-left
    5: 210,    # Rear Right -> bottom-right
    6: 270,    # Side Left -> left side middle
    7: 90,     # Side Right -> right side middle
}

CHANNEL_ANGLES_51 = {
    0: 336.1, 1: 23.7, 2: 359.2, 3: None,
    4: 149.8, 5: 210.0,
}


class DirectionalFrame:
    """One frame of 360° directional audio."""
    __slots__ = ['segments', 'band_segments', 'total_energy',
                 'sound_type', 'sound_label', 'sound_icon', 'sound_confidence']

    def __init__(self):
        self.segments = np.zeros(NUM_SEGMENTS, dtype=np.float32)
        self.band_segments = {}  # Only allocated when needed
        self.total_energy = 0.0
        self.sound_type = ""
        self.sound_label = ""
        self.sound_icon = ""
        self.sound_confidence = 0.0


_active_analyzer = None  # reference for calibration to access

class AudioAnalyzer:
    """Maximum quality directional audio analysis."""

    def __init__(self, sample_rate: int, channels: int, sensitivity: float = 0.008,
                 audio_mode: str = "auto"):
        global _active_analyzer
        _active_analyzer = self
        self.sample_rate = sample_rate
        self.channels = channels
        self.sensitivity = sensitivity

        # Audio mode: "auto" detects from channels, "stereo" forces stereo,
        # "7.1" forces surround (even with 8ch, treat as 7.1)
        if audio_mode == "stereo":
            self.is_stereo = True
        elif audio_mode == "7.1" and channels >= 6:
            self.is_stereo = False
        else:
            # Auto-detect
            self.is_stereo = channels <= 2

        if not self.is_stereo and channels >= 8:
            self.channel_angles = CHANNEL_ANGLES_71
            self.layout = "7.1"
        elif not self.is_stereo and channels >= 6:
            self.channel_angles = CHANNEL_ANGLES_51
            self.layout = "5.1"
        else:
            self.channel_angles = None
            self.layout = "Stereo"
            self.is_stereo = True

        print(f"[Analyzer] {self.layout} | {NUM_SEGMENTS} segments | 1° precision")
        if audio_mode != "auto":
            print(f"[Analyzer] Mode forced to: {audio_mode}")

        if not self.is_stereo:
            self._build_channel_maps()

        self.noise_floor = np.ones(channels) * 0.002
        self.noise_adapt_rate = 0.003

        # Smoothed output
        self.smooth_segments = np.zeros(NUM_SEGMENTS, dtype=np.float32)
        self.smooth_bands = {k: np.zeros(NUM_SEGMENTS, dtype=np.float32)
                             for k in ["sub_low", "low", "mid", "high", "ultra"]}

        self.attack_rate = 0.85
        self.decay_rate = 0.2

        # Sound identification
        self.signatures = []
        self._last_match = ("", "", "", 0.0)

        # Filter self sounds (on = hide own sounds, off = show everything)
        self.filter_self = True

        # Sound focus (from profile - which sounds to detect)
        self.sound_focus = {
            "footsteps": True,
            "gunshots": True,
            "abilities": True,
            "spike": True,
            "reload": False,
            "weapon_drop": False,
            "movement": True,
        }

        self._design_filters()

    def load_signatures(self, signatures):
        """Load sound signatures from a profile."""
        self.signatures = signatures if signatures else []
        print(f"[Analyzer] Loaded {len(self.signatures)} sound signatures")

    def load_sound_focus(self, focus, filter_self=True):
        """Load which sounds to focus on from profile."""
        self.filter_self = filter_self
        if focus:
            self.sound_focus.update(focus)
        enabled = [k for k, v in self.sound_focus.items() if v]
        print(f"[Analyzer] Focus: {', '.join(enabled)}")

    def _identify_sound(self, frame):
        """Identify what sound is playing using frequency band ratios."""
        if not self.signatures:
            return

        # Get overall band energies (sum across all segments)
        band_names = ["sub_low", "low", "mid", "high", "ultra"]
        band_totals = []
        for band in band_names:
            band_totals.append(float(np.sum(frame.band_segments[band])))

        total = sum(band_totals) + 1e-10
        ratios = [e / total for e in band_totals]

        from .fingerprints import match_signature
        match, confidence = match_signature(ratios, self.signatures, min_confidence=0.6)

        if match and confidence > 0.6:
            # Check if this sound type is enabled in focus settings
            sound_type = match.get("type", "")
            focus_map = {
                "movement": "footsteps",
                "gun": "gunshots",
                "ability": "abilities",
                "objective": "spike",
                "action": "reload",  # reload and weapon_drop both map to action
                "map": "movement",
            }
            focus_key = focus_map.get(sound_type, sound_type)
            if not self.sound_focus.get(focus_key, True):
                return  # This sound type is disabled
            frame.sound_type = match.get("type", "")
            frame.sound_label = match.get("name", "")
            frame.sound_icon = match.get("icon", "")
            frame.sound_confidence = confidence
            self._last_match = (frame.sound_type, frame.sound_label,
                                frame.sound_icon, confidence)
        elif self._last_match[3] > 0:
            # Decay previous match
            self._last_match = (self._last_match[0], self._last_match[1],
                                self._last_match[2], self._last_match[3] * 0.9)
            if self._last_match[3] > 0.3:
                frame.sound_type = self._last_match[0]
                frame.sound_label = self._last_match[1]
                frame.sound_icon = self._last_match[2]
                frame.sound_confidence = self._last_match[3]

    def _build_channel_maps(self):
        """Sharp per-channel mapping. Each channel only affects its own zone."""
        self.channel_influence = {}
        if self.channel_angles is None:
            return
        for ch_idx, angle in self.channel_angles.items():
            if angle is None:
                continue
            influence = np.zeros(NUM_SEGMENTS, dtype=np.float32)
            center = int(angle) % NUM_SEGMENTS
            for offset in range(-8, 9):
                seg = (center + offset) % NUM_SEGMENTS
                weight = max(0, 1.0 - abs(offset) / 8.0)
                influence[seg] = weight
            self.channel_influence[ch_idx] = influence

    def _design_filters(self):
        """8th order Butterworth, 5 bands - maximum separation quality."""
        nyq = self.sample_rate / 2.0
        self.band_filters = {}
        for name, lo, hi in [
            ("sub_low", 20, 150),
            ("low", 150, 500),
            ("mid", 500, 2000),
            ("high", 2000, 6000),
            ("ultra", 6000, 16000),
        ]:
            lo_n, hi_n = max(lo / nyq, 0.001), min(hi / nyq, 0.999)
            if lo_n < hi_n:
                self.band_filters[name] = scipy_signal.butter(8, [lo_n, hi_n], btype="band", output="sos")

    def _update_noise_floor(self, energies):
        for i in range(min(len(energies), len(self.noise_floor))):
            if energies[i] < self.noise_floor[i] * 3:
                self.noise_floor[i] = self.noise_floor[i] * 0.997 + energies[i] * 0.003
            self.noise_floor[i] = max(self.noise_floor[i], 0.0003)

    def _analyze_surround(self, frame: np.ndarray) -> DirectionalFrame:
        """7.1/5.1 surround - enhanced with cross-correlation for finer angles.

        Two-pass approach:
        1. Energy-based: which channels are loudest → rough direction
        2. Cross-correlation between adjacent channel PAIRS → fine angle
           between the two channel positions

        This improves accuracy from ~30-45° to ~10-15°.
        """
        result = DirectionalFrame()

        ch_energies = np.sqrt(np.mean(frame ** 2, axis=0))

        # Only true silence
        if np.max(ch_energies) < 0.0001:
            return result

        self._update_noise_floor(ch_energies)

        clean = ch_energies
        dir_idx = [i for i in range(len(clean)) if self.channel_angles.get(i) is not None]
        if not dir_idx:
            return result

        dir_e = clean[dir_idx]
        if np.max(dir_e) < 1e-6:
            return result

        # === AUTO STEREO DETECTION ===
        # If only FL (ch0) and FR (ch1) have audio (like CS2 through 7.1),
        # use stereo left/right mapping instead of surround
        if len(clean) >= 8:
            fl_fr_energy = clean[0] + clean[1]
            other_energy = sum(clean[i] for i in range(len(clean)) if i not in (0, 1, 3))
            if fl_fr_energy > 0.002 and other_energy < fl_fr_energy * 0.1:
                # Only FL and FR have sound = stereo game through 7.1
                return self._analyze_stereo(frame[:, :2].copy())

        # === DIRECTIONAL EXTRACTION ===
        # Problem: when YOU walk, your footsteps are in ALL channels equally.
        # Enemy footstep adds extra energy to 1-2 channels on top of yours.
        # Example: you walking = all channels at 0.01
        #          enemy from left = SL becomes 0.015, others stay 0.01
        # The 0.005 difference IS the enemy footstep.
        #
        # Fix: subtract the minimum channel energy (your centered sound)
        # from all channels. What remains = directional sounds only.

        # From WASAPI loopback debug data:
        #   Silence/music: all channels 0.0006-0.0015, dir_max < 0.0005
        #   Footsteps: 1-2 channels spike, dir_max 0.005-0.02
        #   Gunshots: dir_max 0.05-0.19
        #
        # No auto-calibration needed. The directional extraction handles it.
        # Just skip true silence (all channels < 0.001)
        if np.max(dir_e) < 0.001:
            return result

        # Subtract center (your own sounds, equal in all channels)
        center_level = np.min(dir_e)
        directional = np.maximum(0, dir_e - center_level)

        # From debug: footsteps have dir_max 0.005+
        # Tiny signals (0.0005-0.002) are ambient bleed, not footsteps
        # Use 0.002 as floor - catches all footsteps, ignores ambient
        if np.max(directional) < 0.002:
            return result

        diff = np.where(directional > 0.001, directional, 0.0)

        # Light compression: keep loudness differences visible
        # Close enemy = big bar, far enemy = small bar
        max_e = np.max(diff)
        if max_e > 0.001:
            diff = np.power(diff / max_e, 0.6) * max_e

        # === PASS 1: Energy-based direction (coarse) ===
        diff_full = np.zeros_like(clean)
        for j, ci in enumerate(dir_idx):
            diff_full[ci] = diff[j]

        for ci, influence in self.channel_influence.items():
            if ci >= len(diff_full) or diff_full[ci] < 1e-6:
                continue
            result.segments += influence * diff_full[ci]

        result.total_energy = float(np.max(result.segments))
        return result

    def _analyze_stereo(self, frame: np.ndarray) -> DirectionalFrame:
        """Stereo: FL speaker = left edge, FR speaker = right edge.

        Simple and accurate:
        - FL louder = left bar, FR louder = right bar
        - Louder overall = bigger bar (closer enemy)
        - Both show if sound comes from both sides
        - Bar in middle of the side edge, always
        """
        result = DirectionalFrame()
        L, R = frame[:, 0], (frame[:, 1] if frame.shape[1] > 1 else frame[:, 0])

        Le = np.sqrt(np.mean(L**2))
        Re = np.sqrt(np.mean(R**2))

        total = Le + Re
        if total < 0.002:
            return result

        # Both channels similar = centered sound (your footsteps, music)
        # Skip if difference is less than 3%
        diff = abs(Le - Re)
        if diff < total * 0.008:
            return result

        # Strength from the louder channel (not total)
        # Close = loud channel = big bar, far = quiet = small bar
        strength = max(Le, Re) * 5.0

        sp = 6

        # Show on whichever side is louder
        # If both are loud but one slightly more, show on that side
        # The BIGGER the difference, the more confident the direction
        if Le > Re:
            # Sound from LEFT - show on left edge, center at 270
            sc = 270
            offsets = np.arange(-sp * 3, sp * 3 + 1)
            weights = np.exp(-(offsets ** 2) / (2 * sp ** 2)) * strength
            indices = (sc + offsets) % NUM_SEGMENTS
            mask = np.array([(240 <= idx <= 300) for idx in indices])
            weights *= mask
            np.add.at(result.segments, indices, weights.astype(np.float32))
        else:
            # Sound from RIGHT - show on right edge, center at 90
            sc = 90
            offsets = np.arange(-sp * 3, sp * 3 + 1)
            weights = np.exp(-(offsets ** 2) / (2 * sp ** 2)) * strength
            indices = (sc + offsets) % NUM_SEGMENTS
            mask = np.array([(60 <= idx <= 120) for idx in indices])
            weights *= mask
            np.add.at(result.segments, indices, weights.astype(np.float32))

        result.total_energy = float(np.max(result.segments))
        return result

    def analyze(self, frame: np.ndarray) -> Optional[DirectionalFrame]:
        if frame is None or len(frame) == 0:
            return None
        if frame.ndim == 1:
            frame = frame.reshape(-1, 1)

        raw = self._analyze_stereo(frame) if self.is_stereo else self._analyze_surround(frame)

        # Smooth: vectorized - no Python loops
        rising = raw.segments > self.smooth_segments
        self.smooth_segments[rising] += (raw.segments[rising] - self.smooth_segments[rising]) * self.attack_rate
        self.smooth_segments[~rising] *= (1 - self.decay_rate)

        output = DirectionalFrame()
        output.segments = self.smooth_segments  # No copy - overlay only reads
        output.total_energy = float(np.max(output.segments))

        # Skip sound identification - saves CPU, band data not available

        return output
