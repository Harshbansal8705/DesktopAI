# main.py
import asyncio, edge_tts, os, sys, tempfile, speech_recognition as sr, threading
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

async def speak(text):
    communicate = edge_tts.Communicate(text=text, voice="en-US-RogerNeural", rate="+30%")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
        filename = tmpfile.name
        with SuppressPrint():
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    tmpfile.write(chunk["data"])

    os.system(f"mpg123 {filename}")
    os.remove(filename)

class BackgroundAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.lock = threading.Lock()  # prevent multiple calls simultaneously

        with self.mic as source:
            print("🎙️ Calibrating mic for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("🎙️ Energy threshold set to:", self.recognizer.energy_threshold)

    def callback(self, recognizer, audio):
        # Called whenever a phrase is detected
        threading.Thread(target=self.process_audio, args=(recognizer, audio)).start()

    def process_audio(self, recognizer, audio):
        with self.lock:
            try:
                print("🎤 Recognizing...")
                query = recognizer.recognize_google(audio)
                print(f"🧠 You said: {query}")
            except sr.UnknownValueError:
                print("😕 Sorry, I could not understand audio.")
                return
            except sr.RequestError as e:
                print(f"😞 Could not request results; {e}")
                return

            if query.lower() in ["exit", "quit"]:
                print("👋 Exiting Jarvis...")
                os._exit(0)

            response = agent.invoke(query)
            print(f"🤖 Jarvis: {response}")
            asyncio.run(speak(response["output"]))

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
        while True:
            pass  # Keep main thread alive
    except KeyboardInterrupt:
        assistant.stop_listening()
