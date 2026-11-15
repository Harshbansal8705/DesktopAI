"""Tests voice-to-agent submission without microphone hardware or Groq access."""

import threading
import unittest
from unittest.mock import Mock, patch

import main


class VoiceSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.assistant = main.DesktopAssistant.__new__(main.DesktopAssistant)
        self.assistant.lock = threading.Lock()
        self.assistant.audio_processor = Mock()
        self.assistant.audio_processor.last_error = None
        self.assistant.process_query = Mock()

    @patch.object(main, "overlay")
    def test_recognized_speech_uses_existing_query_pipeline(self, mock_overlay):
        self.assistant.audio_processor.process_audio.return_value = "turn on the lights"

        self.assistant.process_audio(b"audio")

        self.assistant.process_query.assert_called_once_with("turn on the lights")
        mock_overlay.put_message.assert_any_call("status", "Analyzing voice...", "gold")

    @patch.object(main, "overlay")
    def test_failed_transcription_is_not_submitted(self, mock_overlay):
        self.assistant.audio_processor.process_audio.return_value = None

        self.assistant.process_audio(b"audio")

        self.assistant.process_query.assert_not_called()
        mock_overlay.put_message.assert_any_call("status", "Voice transcription failed", "red")


if __name__ == "__main__":
    unittest.main()
