import os, sys, threading, soundfile as sf, numpy as np
from assistant import call_agent
from logger import setup_logger
from ttsplayer import TTSPlayer
from widget import app, overlay
from vad import VoiceActivityDetector
from groq import Groq
from tools import register_stop_assistant
from thread_executor import executor

logger = setup_logger("main", "logs/main.log", level=os.environ["LOG_LEVEL"])


class BackgroundAssistant:
    def __init__(self):
        self.lock = threading.Lock()  # prevent multiple calls simultaneously
        self.speech = TTSPlayer()
        self.speech.start()
        self.vad = VoiceActivityDetector()
        self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

        overlay.start()

    def process_audio(self, audio):
        with self.lock:
            logger.info("Processing audio...")
            temp_file = "temp.wav"
            try:
                # Convert audio bytes to numpy array and save as WAV
                audio_array = np.frombuffer(audio, dtype=np.int16)
                sf.write(temp_file, audio_array, 16000)  # 16000 is the sample rate

                with open(temp_file, "rb") as f:
                    transcription = self.groq_client.audio.transcriptions.create(
                        file=("temp.wav", f.read()),
                        model="distil-whisper-large-v3-en",
                        response_format="text",
                        prompt="Please transcribe the following audio accurately, maintaining proper punctuation and formatting. If you think there is no speech, return empty string."
                    )
                    logger.info(f"Transcription: {transcription}")

                    # Wake word detection: find 'jarvis' anywhere
                    lower_text = transcription.lower()
                    if "jarvis" in lower_text:
                        # Strip everything before 'jarvis'
                        index = lower_text.find("jarvis")
                        query = transcription[index + len("jarvis"):].strip()
                        self.process_query(query)
                    else:
                        logger.debug("🙉 Wake word not detected. Ignoring...")
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

    def process_query(self, query: str):
        overlay.put_message("query", query)
        if query.lower() in ["exit", "quit"]:
            self.shutdown()

        if not query:
            logger.debug("😶 You addressed Jarvis, but gave no command.")
            return

        logger.debug(f"Invoking agent with: {query}")
        overlay.put_message("status", "Processing...", "gold")

        res_msg = call_agent(query)

        logger.info(f"Agent response: {res_msg}")
        overlay.put_message("response", res_msg)
        self.speech.speak(res_msg)

    def start(self):
        logger.info("🔊 Jarvis is listening in the background... Say something!")
        overlay.put_message("status", "Listening...", "skyblue")
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
