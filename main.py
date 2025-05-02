# main.py
import asyncio, edge_tts, os, sys, tempfile, speech_recognition as sr, threading, subprocess
from assistant import agent


class SuppressPrint:
    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr


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
            print("🎙️ Calibrating mic for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            if (self.recognizer.energy_threshold > 500):
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            asyncio.run(self.speak("Energy threshold set to: " + f"{self.recognizer.energy_threshold:.2f}"))
            print("🎙️ Energy threshold set to:", self.recognizer.energy_threshold)

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
            with SuppressPrint():
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
                print("🎤 Recognizing...")
                text = recognizer.recognize_google(audio)
                print(f"🧠 You said: {text}")
            except sr.UnknownValueError:
                print("😕 Sorry, I could not understand audio.")
                return
            except sr.RequestError as e:
                print(f"😞 Could not request results; {e}")
                return

            # Wake word detection: find 'jarvis' anywhere
            lower_text = text.lower()
            if "jarvis" in lower_text:
                # Strip everything before 'jarvis'
                index = lower_text.find("jarvis")
                query = text[index + len("jarvis") :].strip()
            else:
                print("🙉 Wake word not detected. Ignoring...")
                return

            # Check if Jarvis is already speaking
            if self.speaking_process and self.speaking_process.poll() is None:
                self.speaking_process.terminate()
                self.speaking_thread.join()
                self.speaking_process = None

            if query.lower() in ["exit", "quit"]:
                print("👋 Exiting Jarvis...")
                asyncio.run(self.speak("Shutting down!"))
                self.exit_event.set()
                return

            if not query:
                print("😶 You addressed Jarvis, but gave no command.")
                return

            response = agent.invoke(
                {
                    "messages": [
                        {"role": "user", "content": query}
                    ]
                },
                config={"configurable": {"user_name": "Harsh Bansal", "thread_id": "1"}}
            )
            print(f"🤖 Jarvis: {response["messages"][-1].content}")
            asyncio.run(self.speak(response["messages"][-1].content))

    def start(self):
        self.stop = self.recognizer.listen_in_background(self.mic, self.callback)
        print("🔊 Jarvis is listening in the background... Say something!")

    def stop_listening(self):
        if self.stop:
            self.stop(wait_for_stop=False)
            print("🛑 Stopped listening.")


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
