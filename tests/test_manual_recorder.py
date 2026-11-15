"""Unit tests for explicit microphone capture without requiring hardware."""

import unittest
from unittest.mock import patch

import numpy as np

from src.audio.manual_recorder import ManualRecorder, MicrophoneError


class FakeInputStream:
    def __init__(self, **kwargs):
        self.callback = kwargs["callback"]
        self.started = False
        self.stopped = False
        self.closed = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def close(self):
        self.closed = True


class ManualRecorderTests(unittest.TestCase):
    @patch("src.audio.manual_recorder.sd.InputStream", FakeInputStream)
    def test_start_stop_returns_int16_audio(self):
        recorder = ManualRecorder()
        recorder.start()

        stream = recorder._stream
        stream.callback(np.full((5000, 1), 4000, dtype=np.int16), 5000, None, None)
        audio = recorder.stop()

        assert stream.started
        assert stream.stopped
        assert stream.closed
        assert audio.dtype == np.int16
        assert len(audio) == 5000
        assert audio[0] == 4000
        assert not recorder.is_recording

    @patch("src.audio.manual_recorder.sd.InputStream", FakeInputStream)
    def test_stop_without_samples_explains_failure(self):
        recorder = ManualRecorder()
        recorder.start()

        with self.assertRaisesRegex(MicrophoneError, "No microphone audio"):  # noqa: PT027
            recorder.stop()

    @patch("src.audio.manual_recorder.sd.InputStream", FakeInputStream)
    def test_repeated_start_does_not_open_a_second_stream(self):
        recorder = ManualRecorder()
        recorder.start()
        stream = recorder._stream
        recorder.start()

        assert recorder._stream is stream

    @patch("src.audio.manual_recorder.sd.InputStream", FakeInputStream)
    def test_callback_error_is_reported_when_stopping(self):
        recorder = ManualRecorder()
        recorder.start()
        recorder._stream.callback(np.array([[1]], dtype=np.int16), 1, None, "input overflow")

        with self.assertRaisesRegex(MicrophoneError, "input overflow"):  # noqa: PT027
            recorder.stop()

    @patch("src.audio.manual_recorder.sd.InputStream", FakeInputStream)
    def test_silent_microphone_capture_is_rejected(self):
        recorder = ManualRecorder()
        recorder.start()
        recorder._stream.callback(np.zeros((5000, 1), dtype=np.int16), 5000, None, None)

        with self.assertRaisesRegex(MicrophoneError, "No audible microphone input"):  # noqa: PT027
            recorder.stop()


if __name__ == "__main__":
    unittest.main()
