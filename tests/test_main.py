import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure src is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

# Mock third-party dependencies before main is imported
modules_to_mock = [
    "colorama",
    "numpy",
    "soundfile",
    "groq",
    "pyaudio",
    "pydub",
    "pvporcupine",
    "sounddevice",
    "torch",
    "resemblyzer",
    "dotenv",
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "langchain",
    "langchain.chat_models",
    "langchain_core",
    "langchain_core.messages",
    "langchain_core.tools",
    "langchain_core.tools.structured",
    "langchain_core.runnables",
    "langgraph",
    "langgraph.checkpoint",
    "langgraph.checkpoint.sqlite",
    "langgraph.prebuilt",
    "langgraph.prebuilt.chat_agent_executor",
    "adbutils",
    "adbutils.errors",
    "langchain_tavily",
    "PIL",
    "edge_tts",
]

for mod in modules_to_mock:
    sys.modules[mod] = MagicMock()

mock_torch = MagicMock()
mock_torch.hub.load.return_value = (
    MagicMock(),
    (MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()),
)
sys.modules["torch"] = mock_torch

# Mock sqlite3.connect so it doesn't fail on missing checkpoints directory
mock_sqlite3 = MagicMock()
mock_sqlite3.connect.return_value = MagicMock()
sys.modules["sqlite3"] = mock_sqlite3


class TestProcessAudioValidation(unittest.TestCase):
    @patch("main.TTSPlayer")
    @patch("main.AudioProcessor")
    @patch("main.Listener")
    @patch("main.overlay")
    def test_process_audio_with_invalid_transcriptions(
        self, mock_overlay, mock_listener, mock_audio_processor, mock_tts_player
    ):
        from main import DesktopAssistant

        assistant = DesktopAssistant()
        assistant.process_query = MagicMock()

        # Test cases for invalid transcriptions: None, empty string, whitespace string
        invalid_outputs = [None, "", "   ", "\n\t "]

        for sample in invalid_outputs:
            with self.subTest(sample=sample):
                assistant.audio_processor.process_audio.return_value = sample
                assistant.process_audio(b"dummy_audio_data")

                # Verify process_query was not called
                assistant.process_query.assert_not_called()
                # Verify overlay status set to error indicator
                mock_overlay.put_message.assert_called_with(
                    "status", "Could not transcribe audio", "red"
                )
                assistant.process_query.reset_mock()

    @patch("main.TTSPlayer")
    @patch("main.AudioProcessor")
    @patch("main.Listener")
    @patch("main.overlay")
    def test_process_audio_with_valid_transcription(
        self, mock_overlay, mock_listener, mock_audio_processor, mock_tts_player
    ):
        from main import DesktopAssistant

        assistant = DesktopAssistant()
        assistant.process_query = MagicMock()

        valid_transcription = "Hello Jasper, what is the weather today?"
        assistant.audio_processor.process_audio.return_value = valid_transcription

        assistant.process_audio(b"dummy_audio_data")

        # Verify process_query was called with valid transcription
        assistant.process_query.assert_called_once_with(valid_transcription)


if __name__ == "__main__":
    unittest.main()
