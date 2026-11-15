"""Tests for Groq transcription boundaries without a network request."""

import unittest
from unittest.mock import Mock, mock_open, patch

import numpy as np

from src.audio.audio_processor import AudioProcessor


class AudioProcessorTests(unittest.TestCase):
    def setUp(self):
        self.processor = AudioProcessor.__new__(AudioProcessor)
        self.processor.groq_client = Mock()
        self.processor.last_error = None

    @patch("src.audio.audio_processor.os.path.exists", return_value=False)
    @patch("src.audio.audio_processor.sf.write")
    @patch("builtins.open", new_callable=mock_open, read_data=b"wav-data")
    def test_returns_groq_transcription(self, mock_file, mock_write, mock_exists):
        self.processor.groq_client.audio.transcriptions.create.return_value = "recognized request"

        result = self.processor.process_audio(np.full(16000, 4000, dtype=np.int16))

        assert result == "recognized request"
        mock_write.assert_called_once()
        mock_file.assert_called_once()
        assert mock_exists.called
        request = self.processor.groq_client.audio.transcriptions.create.call_args.kwargs
        assert request["model"] == "whisper-large-v3-turbo"
        assert request["language"] == "en"

    @patch("src.audio.audio_processor.os.path.exists", return_value=False)
    @patch("src.audio.audio_processor.sf.write", side_effect=OSError("disk unavailable"))
    def test_returns_none_when_audio_cannot_be_written(self, mock_write, mock_exists):
        result = self.processor.process_audio(np.full(16000, 4000, dtype=np.int16))

        assert result is None
        mock_write.assert_called_once()
        assert mock_exists.called
        assert self.processor.last_error == "disk unavailable"

    @patch("src.audio.audio_processor.os.path.exists", return_value=False)
    def test_silent_audio_is_rejected_before_api_call(self, mock_exists):
        result = self.processor.process_audio(np.zeros(16000, dtype=np.int16))

        assert result is None
        assert "silent" in self.processor.last_error
        self.processor.groq_client.audio.transcriptions.create.assert_not_called()
        assert mock_exists.called
