import os, sys, threading, soundfile as sf, numpy as np
from assistant import call_agent
from audio_processor import AudioProcessor
from logger import setup_logger
from ttsplayer import TTSPlayer
from widget import app, overlay
from vad import VoiceActivityDetector
from groq import Groq
from tools import register_stop_assistant
from config import config
from thread_executor import executor

logger = setup_logger("main", "logs/main.log", level=os.environ["LOG_LEVEL"])


class BackgroundAssistant:
    def __init__(self):
        self.lock = threading.Lock()  # prevent multiple calls simultaneously
        self.speech = TTSPlayer()
        self.speech.start()
        # Initialize audio processor and VAD
        self.audio_processor = AudioProcessor()
        self.vad = VoiceActivityDetector(tts_player=self.speech, overlay=overlay)
        overlay.on_new_message = self.process_query
        overlay.start()

    def process_audio(self, audio):
        with self.lock:
            logger.info("Processing audio...")
            overlay.put_message("status", "Analyzing voice...", "gold")
            transcription = self.audio_processor.process_audio(audio)
            self.process_query(transcription)

    def process_query(self, query: str):
        overlay.put_message("query", query)

        logger.debug(f"Invoking agent with: {query}")
        overlay.put_message("status", "Processing...", "gold")

        res_msg = call_agent(query)

        logger.info(f"Agent response: {res_msg}")
        overlay.put_message("response", res_msg)
        overlay.put_message("status", "Active", "green")
        self.speech.speak(res_msg)

    def start(self):
        logger.info("🔊 Jarvis is listening in the background... Say something!")
        overlay.put_message("status", "Active", "green")
        executor.submit(self.vad.on_speech, self.process_audio)

    def shutdown(self):
        self.speech.speak("Shutting down!")
        overlay.put_message("status", "Shutting down...", "red")
        logger.info("Shutting down")
        self.vad.stop_listening()
        self.speech.shutdown()
        executor.shutdown(wait=False, cancel_futures=True)
        overlay.close()

# Run the assistant
if __name__ == "__main__":
    assistant = BackgroundAssistant()
    register_stop_assistant(assistant.shutdown)
    assistant.start()
    app.exec()
