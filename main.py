"""
DesktopAI Assistant - Clean and Modular Voice Assistant

This is the main entry point for the DesktopAI assistant with a clean modular architecture.
"""

import argparse
import os
import sys

# Add the src directory to Python path for easy imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import threading

from src import config
from src.core.assistant import call_agent
from src.core.tools import register_stop_assistant
from src.ui.overlay import app, overlay
from src.utils.logger import get_logger
from src.utils.thread_executor import executor

logger = get_logger()


class DesktopAssistant:
    """Main DesktopAI Assistant class with clean modular architecture."""

    def __init__(self, text_only: bool = False, no_tts: bool = False):
        """Initialize the assistant with all required components."""
        self.text_only = text_only
        self.no_tts = no_tts or text_only
        config.TEXT_ONLY_MODE = text_only
        config.NO_TTS = self.no_tts
        self.lock = threading.Lock()
        self._setup_components()
        self._setup_ui()

    def _setup_components(self):
        """Initialize core components."""
        self.speech = None
        if not self.no_tts:
            from src.audio.ttsplayer import TTSPlayer

            self.speech = TTSPlayer()
            self.speech.start()

        self.audio_processor = None
        self.listener = None
        if not self.text_only:
            from src.audio.audio_processor import AudioProcessor
            from src.audio.listener import Listener

            self.audio_processor = AudioProcessor()
            self.listener = Listener(tts_player=self.speech, overlay=overlay)

    def _setup_ui(self):
        """Setup user interface."""
        self.overlay = overlay
        self.overlay.on_new_message = self.process_query
        self.overlay.start()

    def _speak(self, text):
        if self.speech is not None:
            self.speech.speak(text)

    def process_audio(self, audio):
        """Process incoming audio data."""
        if self.audio_processor is None:
            logger.error("Audio processing is unavailable in text-only mode.")
            return

        with self.lock:
            logger.info("Processing audio...")
            self.overlay.put_message("status", "Analyzing voice...", "gold")
            transcription = self.audio_processor.process_audio(audio)
            self.process_query(transcription)

    def process_query(self, query: str):
        """Process the text query."""
        self.overlay.put_message("query", query)
        confirmation = self.overlay.resolve_voice_confirmation(query)
        if confirmation is not None:
            response = "Execution confirmed. Running the command." if confirmation else "Execution cancelled by user."
            self.overlay.put_message("response", response)
            self.overlay.put_message("status", "Active", "green")
            self._speak(response)
            return

        logger.debug(f"Invoking agent with: {query}")
        self.overlay.put_message("status", "Processing...", "gold")
        try:
            response = call_agent(query)
            logger.info(f"Agent response: {response}")
            self.overlay.put_message("response", response)
            self.overlay.put_message("status", "Active", "green")
            self._speak(response)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            self.overlay.put_message("status", "Error occurred", "red")
            self._speak("Sorry, an error occurred while processing your request.")

    def start(self):
        """Start the assistant."""
        if self.listener is not None:
            logger.info("🔊 Listening in the background... Say something!")
            executor.submit(self.listener.listen, self.process_audio)
        else:
            logger.info("Text-only mode active. Enter a message in the overlay.")
        self.overlay.put_message("status", "Active", "green")

    def shutdown(self):
        """Clean shutdown of the assistant."""
        self._speak("Shutting down!")
        self.overlay.put_message("status", "Shutting down...", "red")
        logger.info("Shutting down...")

        if self.listener is not None:
            self.listener.stop_listening()
        if self.speech is not None:
            self.speech.shutdown()
        executor.shutdown(wait=False, cancel_futures=True)
        self.overlay.close()


def main():
    """Main function to run Desktop Assistant."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--text-only",
        action="store_true",
        default=False,
        help="Run in text-only mode without microphone or audio dependencies",
    )
    parser.add_argument(
        "--no-tts",
        action="store_true",
        default=False,
        help="Disable Text-To-Speech output",
    )
    args = parser.parse_args()

    config.TEXT_ONLY_MODE = args.text_only
    config.NO_TTS = args.no_tts

    assistant = DesktopAssistant(text_only=args.text_only, no_tts=args.no_tts)
    register_stop_assistant(assistant.shutdown)
    assistant.start()
    app.exec()


if __name__ == "__main__":
    main()
