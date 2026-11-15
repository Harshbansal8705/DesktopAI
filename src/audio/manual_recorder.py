"""On-demand microphone capture for platforms without a wake-word model."""

import threading
from contextlib import suppress

import numpy as np
import sounddevice as sd

from src.config import config
from src.utils.logger import get_logger

logger = get_logger()


class MicrophoneError(RuntimeError):
    """Raised when an input device cannot be opened or produces no audio."""


class ManualRecorder:
    """Capture int16 microphone samples between explicit start and stop actions."""

    def __init__(self):
        self._lock = threading.Lock()
        self._frames: list[np.ndarray] = []
        self._stream = None
        self._recording = False
        self._callback_error: str | None = None

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._recording

    def _capture(self, indata, frames, time_info, status):
        """Store a copy because sounddevice reuses its callback buffer."""
        del frames, time_info
        with self._lock:
            if status:
                self._callback_error = str(status)
            if self._recording:
                self._frames.append(indata.copy())

    def start(self) -> None:
        """Open and begin the default input stream, triggering macOS permission if needed."""
        with self._lock:
            if self._recording:
                return
            self._frames = []
            self._callback_error = None
            try:
                stream = sd.InputStream(
                    channels=config.CHANNELS,
                    samplerate=config.SAMPLE_RATE,
                    dtype="int16",
                    blocksize=config.NUM_SAMPLES,
                    callback=self._capture,
                )
                self._recording = True
                stream.start()
                self._stream = stream
            except Exception as exc:
                self._recording = False
                self._stream = None
                raise MicrophoneError(f"Could not access the microphone: {exc}") from exc

    def stop(self) -> np.ndarray:
        """Stop capture and return mono int16 audio for ``AudioProcessor``."""
        with self._lock:
            if not self._recording:
                raise MicrophoneError("Voice recording is not active.")
            self._recording = False
            stream = self._stream
            self._stream = None
            frames = self._frames
            self._frames = []
            callback_error = self._callback_error
            self._callback_error = None

        try:
            stream.stop()
            stream.close()
        except Exception as exc:
            raise MicrophoneError(f"Could not stop microphone capture: {exc}") from exc

        if callback_error:
            raise MicrophoneError(f"Microphone capture error: {callback_error}")
        if not frames:
            raise MicrophoneError("No microphone audio was captured. Please try again.")

        audio = np.concatenate(frames, axis=0).reshape(-1)
        duration = len(audio) / config.SAMPLE_RATE
        normalized = audio.astype(np.float32) / np.iinfo(np.int16).max
        rms = float(np.sqrt(np.mean(np.square(normalized))))
        peak = float(np.max(np.abs(normalized)))
        logger.info(
            "Microphone capture: %.2fs, %d samples, %d bytes, int16 mono/%dHz, rms=%.5f, peak=%.5f",
            duration,
            len(audio),
            audio.nbytes,
            config.SAMPLE_RATE,
            rms,
            peak,
        )
        if duration < config.MIN_RECORDING_SECONDS:
            raise MicrophoneError(
                f"Recording was too short ({duration:.2f}s). Hold recording for at least "
                f"{config.MIN_RECORDING_SECONDS:.2f}s."
            )
        if rms < config.SILENCE_RMS_THRESHOLD:
            raise MicrophoneError(
                "No audible microphone input was detected. Check the selected input device and macOS Microphone permission."
            )
        return audio

    def cancel(self) -> None:
        """Release an active stream without submitting audio."""
        if not self.is_recording:
            return
        with suppress(MicrophoneError):
            self.stop()
