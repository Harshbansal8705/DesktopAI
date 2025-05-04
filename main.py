import os, speech_recognition as sr, threading
from assistant import agent
from logger import setup_logger
from ttsplayer import TTSPlayer

logger = setup_logger("main", "logs/main.log", level=os.getenv("LOG_LEVEL", "INFO"))


class BackgroundAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.lock = threading.Lock()  # prevent multiple calls simultaneously
        self.recognizer.pause_threshold = 2
        self.recognizer.non_speaking_duration = 0.5
        self.speech = TTSPlayer()
        self.speech.start()
        self.exit_event = threading.Event()

        with self.mic as source:
            self.speech.speak("Calibrating mic for ambient noise...")
            logger.info("🎙️ Calibrating mic for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            if self.recognizer.energy_threshold > 500:
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
        with self.lock:
            try:
                logger.debug("Recognizing speech...")
                text = recognizer.recognize_google(audio)
                logger.info(f"Recognized: {text}")
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

            if query.lower() in ["exit", "quit"]:
                logger.info("👋 Exiting Jarvis...")
                self.speech.speak("Shutting down!")
                self.exit_event.set()
                return

            if not query:
                logger.debug("😶 You addressed Jarvis, but gave no command.")
                return

            logger.debug(f"Invoking agent with: {query}")
            response = agent.invoke(
                {"messages": [{"role": "user", "content": query}]},
                config={
                    "configurable": {"user_name": "Harsh Bansal", "thread_id": "1"}
                },
            )

            # Handle the case when response["messages"][-1].content is a list of messages
            res_msg = response["messages"][-1].content
            if isinstance(res_msg, list):
                res_msg = "\n".join([msg.content for msg in res_msg])

            logger.info(f"Agent response: {res_msg}")
            self.speech.speak(res_msg)

    def start(self):
        self.stop = self.recognizer.listen_in_background(self.mic, self.callback)
        logger.info("🔊 Jarvis is listening in the background... Say something!")

    def stop_listening(self):
        if self.stop:
            self.stop(wait_for_stop=False)
            logger.info("🛑 Stopped listening.")
        self.speech.shutdown()

        self.exit_event.set()


# Run the assistant
if __name__ == "__main__":
    assistant = BackgroundAssistant()
    assistant.start()
    assistant.exit_event.wait()
    assistant.stop_listening()
    exit(0)
