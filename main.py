import os, speech_recognition as sr, sys, threading
from assistant import agent
from logger import setup_logger
from ttsplayer import TTSPlayer
from widget import app, overlay

logger = setup_logger("main", "logs/main.log", level=os.environ["LOG_LEVEL"])


class BackgroundAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.lock = threading.Lock()  # prevent multiple calls simultaneously
        self.recognizer.pause_threshold = 2
        self.recognizer.non_speaking_duration = 0.5
        self.speech = TTSPlayer()
        self.speech.start()

        overlay.start()

        with self.mic as source:
            self.speech.speak("Calibrating mic for ambient noise...")
            logger.info("🎙️ Calibrating mic for ambient noise...")
            overlay.put_message("status", "Calibrating Mic...", "yellow")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)

            calibration_msg = (
                f"Energy threshold set to: {self.recognizer.energy_threshold:.2f}"
            )
            self.speech.speak(calibration_msg)
            logger.info(f"🎙️ {calibration_msg}")

    def callback(self, recognizer, audio):
        # Called whenever a phrase is detected
        threading.Thread(target=self.process_audio, args=(recognizer, audio)).start()

    def process_audio(self, recognizer, audio):
        try:
            with self.lock:
                try:
                    logger.debug("Recognizing speech...")
                    text = recognizer.recognize_google(audio)
                    logger.debug(f"Recognized: {text}")
                except sr.UnknownValueError:
                    logger.debug("😕 Sorry, I could not understand audio.")
                    return
                except sr.RequestError as e:
                    logger.error(f"RequestError: {e}")
                    return

                # Wake word detection: find 'jarvis' anywhere
                lower_text = text.lower()
                if "jarvis" in lower_text:
                    # Strip everything before 'jarvis'
                    index = lower_text.find("jarvis")
                    query = text[index + len("jarvis") :].strip()
                else:
                    logger.debug("🙉 Wake word not detected. Ignoring...")
                    return

                self.process_query(query)
        except Exception as e:
            logger.error(f"[process_audio] Unexpected error: {e}")
            overlay.put_message(
                "status", f"[process_audio] Unexpected error: {e}", "red"
            )

    def process_query(self, query: str):
        overlay.put_message("query", query)
        if query.lower() in ["exit", "quit"]:
            self.shutdown()

        if not query:
            logger.debug("😶 You addressed Jarvis, but gave no command.")
            return

        logger.debug(f"Invoking agent with: {query}")
        overlay.put_message("status", "Processing...", "gold")
        response = agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"configurable": {"user_name": "Harsh Bansal", "thread_id": "1"}},
        )

        # Handle the case when response["messages"][-1].content is a list of messages
        res_msg = response["messages"][-1].content
        if isinstance(res_msg, list):
            res_msg = "\n".join([msg.content for msg in res_msg])

        logger.info(f"Agent response: {res_msg}")
        overlay.put_message("response", res_msg)
        self.speech.speak(res_msg)

    def start(self):
        self.stop = self.recognizer.listen_in_background(self.mic, self.callback)
        logger.info("🔊 Jarvis is listening in the background... Say something!")
        overlay.put_message("status", "Listening...", "skyblue")

    def shutdown(self):
        self.speech.speak("Shutting down!")
        overlay.put_message("status", "Shutting down...", "red")
        logger.info("Shutting down")
        if self.stop:
            self.stop(wait_for_stop=False)
            logger.debug("🛑 Stopped listening.")
        overlay.close()
        self.speech.shutdown()


# Run the assistant
if __name__ == "__main__":
    assistant = BackgroundAssistant()
    assistant.start()
    sys.exit(app.exec())
