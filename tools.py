# tools.py
import subprocess, ast
from langchain.tools import tool
import pyttsx3
from typing import Optional

engine = pyttsx3.init()


def speak(text):
    """Function to speak out the provided text"""
    engine.say(text)
    engine.runAndWait()


@tool
def run_command(command: str) -> str:
    """Run a shell command on the local Linux machine."""
    try:
        output = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, text=True
        )
        return f"Command executed:\n{output}"
    except subprocess.CalledProcessError as e:
        return f"Error:\n{e.output}"


@tool
def open_google_chrome(params: dict) -> str:
    """
    Open Google Chrome with the specified URL.

    Parameters:
    - url (str): URL to open.
    - new_window (python bool: optional): Whether to open in a new window (True | False) Default = False.
    """
    # params = ast.literal_eval(params)
    url: Optional[str] = params.get("url")
    new_window: str = params.get("new_window", "False")
    print(params)

    if url:
        command = f"google-chrome-stable {'--new-window' if new_window.lower() == "true" else ''} {url}"
    else:
        command = "google-chrome-stable"

    try:
        subprocess.Popen(command, shell=True)
        return f"Google Chrome opened with URL: {url}"
    except Exception as e:
        return f"Error opening Google Chrome: {e}"
