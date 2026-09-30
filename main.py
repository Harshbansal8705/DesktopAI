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

from src.core.assistant import call_agent
from src.core.tools import register_stop_assistant
from src.ui.overlay import app, overlay
from src.utils.logger import get_logger
from src.utils.thread_executor import executor

logger = get_logger()


class DesktopAssistant:
    """Main DesktopAI Assistant class with clean modular architecture."""

    def __init__(self, text_only=False):
        """Initialize the assistant with all required components."""
        self.lock = threading.Lock()
        self.text_only = text_only
        self._setup_components()
        self._setup_ui()

    def _setup_components(self):
        """Initialize core components."""
        if not self.text_only:
            from src.audio.audio_processor import AudioProcessor
            from src.audio.listener import Listener
            from src.audio.ttsplayer import TTSPlayer

            self.speech = TTSPlayer()
            self.speech.start()
            self.audio_processor = AudioProcessor()
            self.listener = Listener(tts_player=self.speech, overlay=overlay)
        else:
            self.speech = None
            self.audio_processor = None
            self.listener = None
            logger.info("Running in text-only mode — microphone and TTS disabled")

    def _setup_ui(self):
        """Setup user interface."""
        overlay.on_new_message = self.process_query
        overlay.start()

    def process_audio(self, audio):
        """Process incoming audio data."""
        with self.lock:
            logger.info("Processing audio...")
            overlay.put_message("status", "Analyzing voice...", "gold")
            transcription = self.audio_processor.process_audio(audio)
            if not transcription or not transcription.strip():
                logger.warning("Transcription returned empty or None, skipping.")
                overlay.put_message("status", "Couldn't hear that", "orange")
                return
            self.process_query(transcription)

    def process_query(self, query: str):
        """Process the text query."""
        overlay.put_message("query", query)
        logger.debug(f"Invoking agent with: {query}")
        overlay.put_message("status", "Processing...", "gold")
        try:
            response = call_agent(query)
            logger.info(f"Agent response: {response}")
            overlay.put_message("response", response)
            overlay.put_message("status", "Active", "green")
            if self.speech:
                self.speech.speak(response)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            overlay.put_message("status", "Error occurred", "red")
            if self.speech:
                self.speech.speak("Sorry, an error occurred while processing your request.")

    def start(self):
        """Start the assistant."""
        if self.text_only:
            logger.info("Text-only mode active — type in the overlay to interact")
            overlay.put_message("status", "Text Mode Active", "cyan")
        else:
            logger.info("Listening in the background... Say something!")
            overlay.put_message("status", "Active", "green")
            executor.submit(self.listener.listen, self.process_audio)

    def shutdown(self):
        """Clean shutdown of the assistant."""
        if self.speech:
            self.speech.speak("Shutting down!")
        overlay.put_message("status", "Shutting down...", "red")
        logger.info("Shutting down...")

        if self.listener:
            self.listener.stop_listening()
        if self.speech:
            self.speech.shutdown()
        executor.shutdown(wait=False, cancel_futures=True)
        overlay.close()


def main():
    """Main function to run Desktop Assistant."""
    parser = argparse.ArgumentParser(description="DesktopAI Assistant")
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Run without microphone, wake word, or TTS — type-only interaction",
    )
    args = parser.parse_args()

    assistant = DesktopAssistant(text_only=args.text_only)
    register_stop_assistant(assistant.shutdown)
    assistant.start()
    app.exec()


if __name__ == "__main__":
    main()
