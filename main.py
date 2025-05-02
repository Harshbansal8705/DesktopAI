# main.py
import asyncio, edge_tts, os, tempfile, speech_recognition as sr, threading, subprocess
from assistant import agent
from logger import setup_logger

logger = setup_logger("main", "logs/main.log", level=os.getenv("LOG_LEVEL", "INFO"))


class BackgroundAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.lock = threading.Lock()  # prevent multiple calls simultaneously
        self.recognizer.pause_threshold = 1
        self.recognizer.non_speaking_duration = 0.5
        self.speaking_process = None
        self.speaking_thread = None
        self.exit_event = threading.Event()

        with self.mic as source:
            asyncio.run(self.speak("Calibrating mic for ambient noise..."))
            logger.info("🎙️ Calibrating mic for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            if self.recognizer.energy_threshold > 500:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            asyncio.run(
                self.speak(
                    "Energy threshold set to: "
                    + f"{self.recognizer.energy_threshold:.2f}"
                )
            )
            logger.info(f"🎙️ Energy threshold set to: {self.recognizer.energy_threshold}")

    def _play_audio(self, filename):
        self.speaking_process = subprocess.Popen(["mpg123", "-q", filename])
        self.speaking_process.wait()
        self.speaking_process = None
        os.remove(filename)

    async def speak(self, text):
        communicate = edge_tts.Communicate(
            text=text, voice="en-US-RogerNeural", rate="+30%"
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
            filename = tmpfile.name
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    tmpfile.write(chunk["data"])

        # Play audio in a background thread (non-blocking)
        self.speaking_thread = threading.Thread(
            target=self._play_audio, args=(filename,)
        )
        self.speaking_thread.start()

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

            # Check if Jarvis is already speaking
            if self.speaking_process and self.speaking_process.poll() is None:
                self.speaking_process.terminate()
                self.speaking_thread.join()
                self.speaking_process = None

            if query.lower() in ["exit", "quit"]:
                logger.info("👋 Exiting Jarvis...")
                asyncio.run(self.speak("Shutting down!"))
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
            asyncio.run(self.speak(res_msg))

    def start(self):
        self.stop = self.recognizer.listen_in_background(self.mic, self.callback)
        logger.info("🔊 Jarvis is listening in the background... Say something!")

    def stop_listening(self):
        if self.stop:
            self.stop(wait_for_stop=False)
            logger.info("🛑 Stopped listening.")


# Run the assistant
if __name__ == "__main__":
    assistant = BackgroundAssistant()
    assistant.start()

    try:
        while not assistant.exit_event.is_set():
            pass  # Keep main thread alive
    except KeyboardInterrupt:
        assistant.stop_listening()
    finally:
        assistant.stop_listening()
        exit(0)
