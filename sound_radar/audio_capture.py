"""WASAPI Loopback audio capture - zero conversion, maximum speed.

Captures the exact audio stream your headset receives via WASAPI loopback.
Same sample rate, same channels, same bit depth. No resampling.

Spec: 6000Hz update rate (0.17ms per block at 48kHz)
"""

import queue
import numpy as np
import pyaudiowpatch as pyaudio
from .error_handler import DeviceNotFoundError, WASAPINotAvailableError, AudioStreamError


class AudioCapture:
    """Captures audio from WASAPI loopback - what you hear = what we capture."""

    def __init__(self, device_index=None, block_size=8):
        self.device_index = device_index
        self.block_size = block_size
        self.audio_queue = queue.Queue(maxsize=64)  # small buffer, low memory
        self._running = False
        self._stream = None
        self._pa = None

        self.sample_rate = None
        self.channels = None
        self.device_name = None

    def find_loopback_device(self):
        """Find the WASAPI loopback device for the default output."""
        self._pa = pyaudio.PyAudio()

        # Always auto-detect the best loopback device
        # Prefer highest channel count (7.1 > 5.1 > stereo)

        try:
            wasapi_info = self._pa.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            raise WASAPINotAvailableError(
                "WASAPI is not available on this system.\n"
                "SoundSight requires Windows 10 or 11."
            )

        # Find the best loopback device automatically
        # Priority: most channels (7.1 > 5.1 > stereo)
        best_dev = None
        best_channels = 0

        for i in range(self._pa.get_device_count()):
            dev = self._pa.get_device_info_by_index(i)
            if dev.get("isLoopbackDevice", False):
                ch = dev["maxInputChannels"]
                if ch > best_channels:
                    best_channels = ch
                    best_dev = dev

        if best_dev is not None:
            return best_dev

        raise DeviceNotFoundError(
            "No audio loopback device found.\n\n"
            "Make sure your headset is connected and set as\n"
            "the default output in Windows Sound Settings."
        )

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio thread callback - converts and queues audio data."""
        audio_data = np.frombuffer(in_data, dtype=np.float32).reshape(-1, self.channels)
        try:
            self.audio_queue.put_nowait(audio_data)
        except queue.Full:
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.audio_queue.put_nowait(audio_data)
            except queue.Full:
                pass
        return (None, pyaudio.paContinue)

    def start(self):
        """Start capturing - matches device's native settings exactly."""
        dev_info = self.find_loopback_device()
        self.channels = dev_info["maxInputChannels"]
        self.sample_rate = int(dev_info["defaultSampleRate"])
        self.device_name = dev_info["name"]

        update_rate = self.sample_rate / self.block_size
        latency_ms = self.block_size / self.sample_rate * 1000

        print(f"[Capture] Device: {self.device_name}")
        print(f"[Capture] Sample rate: {self.sample_rate} Hz")
        print(f"[Capture] Channels: {self.channels}")
        print(f"[Capture] Block: {self.block_size} samples ({latency_ms:.2f}ms)")
        print(f"[Capture] Update rate: {update_rate:.0f} Hz")

        self._stream = self._pa.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=dev_info["index"],
            frames_per_buffer=self.block_size,
            stream_callback=self._audio_callback,
        )
        self._stream.start_stream()
        self._running = True

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._pa:
            self._pa.terminate()
            self._pa = None

    def get_frame(self, timeout=0.05):
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
