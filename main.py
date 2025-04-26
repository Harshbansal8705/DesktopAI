# main.py
from assistant import agent
import asyncio, edge_tts, os, sys, tempfile, speech_recognition as sr


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


def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        audio = r.listen(source)

    try:
        text = r.recognize_google(audio)
        print(f"🧠 You said: {text}")
        return text
    except sr.UnknownValueError:
        print("😕 Sorry, I could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"😞 Could not request results; {e}")
        return ""


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

a = True

while True:
    query = input("\n🧠 Ask Jarvis: ")
    # query = listen()
    if not query:
        continue
    # if a:
    #     query = listen()
    #     a = False
    # else:
    #     query = input("\n🧠 Ask Jarvis: ")
    if query.lower() in ["exit", "quit"]:
        break
    response = agent.invoke(query)
    print(f"🤖 Jarvis: {response}")
    asyncio.run(speak(response["output"]))  # Speak the response
    # print_and_speak(response)  # Speak the response
    # print(f"🗣️ Jarvis: {response}")
