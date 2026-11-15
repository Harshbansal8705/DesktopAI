"""
DesktopAI Assistant - Clean and Modular Voice Assistant

This is the main entry point for the DesktopAI assistant with a clean modular architecture.
"""

import os
import sys

# Add the src directory to Python path for easy imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import threading

from src.audio.audio_processor import AudioProcessor
from src.audio.manual_recorder import ManualRecorder, MicrophoneError
from src.audio.ttsplayer import TTSPlayer
from src.config import config
from src.core.assistant import call_agent
from src.core.tools import register_stop_assistant
from src.ui.overlay import app, overlay
from src.utils.logger import get_logger
from src.utils.thread_executor import executor

logger = get_logger()


class DesktopAssistant:
    """Main DesktopAI Assistant class with clean modular architecture."""

    def __init__(self):
        """Initialize the assistant with all required components."""
        self.lock = threading.Lock()
        self._shutting_down = False
        self._setup_components()
        self._setup_ui()

    def _setup_components(self):
        """Initialize core components."""
        # Text-to-Speech
        self.speech = TTSPlayer()
        self.speech.start()

        # Audio processing
        self.audio_processor = AudioProcessor()
        self.manual_recorder = ManualRecorder()
        self.listener = None
        if config.WAKE_WORD_ENABLED:
            # Import lazily: the listener's optional voice-verification stack
            # should not be required for text-only operation on macOS.
            from src.audio.listener import Listener

            self.listener = Listener(tts_player=self.speech, overlay=overlay)
        else:
            logger.info("Wake-word detection is disabled; use the overlay text input to submit requests.")

    def _setup_ui(self):
        """Setup user interface."""
        overlay.on_new_message = self.process_query
        overlay.on_recording_toggled = self.handle_manual_recording
        overlay.exit_callback = self.shutdown
        overlay.start()

    def process_audio(self, audio):
        """Process incoming audio data."""
        with self.lock:
            logger.info("Processing audio...")
            overlay.put_message("status", "Analyzing voice...", "gold")
            transcription = self.audio_processor.process_audio(audio)
            if not transcription:
                detail = self.audio_processor.last_error or "no speech could be transcribed"
                logger.error("Speech transcription did not return text: %s", detail)
                overlay.put_message("response", f"Voice input failed: {detail}")
                overlay.put_message("status", "Voice transcription failed", "red")
                return
            self.process_query(transcription)

    def handle_manual_recording(self, should_record: bool):
        """Start or stop explicit microphone capture from the overlay control."""
        if should_record:
            try:
                self.manual_recorder.start()
            except MicrophoneError as exc:
                self._report_microphone_error(exc)
                return
            overlay.put_message("recording", True)
            overlay.put_message("status", "Recording… click Stop voice when finished", "skyblue")
            return

        try:
            audio = self.manual_recorder.stop()
        except MicrophoneError as exc:
            self._report_microphone_error(exc)
            return

        overlay.put_message("recording", False)
        overlay.put_message("status", "Transcribing voice…", "gold")
        self.process_audio(audio)

    def _report_microphone_error(self, error: Exception):
        message = f"Microphone unavailable: {error}"
        if config.PLATFORM == "Darwin":
            message += " Allow this terminal or IDE in System Settings > Privacy & Security > Microphone."
        logger.error(message)
        overlay.put_message("recording", False)
        overlay.put_message("response", message)
        overlay.put_message("status", "Microphone error", "red")

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
            self.speech.speak(response)
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            overlay.put_message("response", f"Error: {e}")
            overlay.put_message("status", "Error occurred", "red")
            self.speech.speak("Sorry, an error occurred while processing your request.")

    def start(self):
        """Start the assistant."""
        if self.listener:
            logger.info("🔊 Listening in the background... Say something!")
            overlay.put_message("status", "Active", "green")
            executor.submit(self.listener.listen, self.process_audio)
        else:
            logger.info("Wake word is disabled. Use text input or Start voice in the overlay.")
            overlay.put_message("status", "Wake word disabled — use text or voice", "gold")

    def shutdown(self):
        """Clean shutdown of the assistant."""
        if self._shutting_down:
            return
        self._shutting_down = True
        self.speech.speak("Shutting down!")
        overlay.put_message("status", "Shutting down...", "red")
        logger.info("Shutting down...")

        if self.listener:
            self.listener.stop_listening()
        self.manual_recorder.cancel()
        self.speech.shutdown()
        executor.shutdown(wait=False, cancel_futures=True)
        # Avoid recursing when this shutdown was initiated by the window close.
        overlay.exit_callback = None
        overlay.close()


def main():
    """Main function to run Desktop Assistant."""
    assistant = DesktopAssistant()
    register_stop_assistant(assistant.shutdown)
    assistant.start()
    exit_code = app.exec()
    logger.info("Qt event loop exited with code %s", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
