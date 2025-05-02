# tools.py
import subprocess
from langchain.tools import tool


@tool
def run_command(command: str) -> str:
    """Run a shell command on the local Linux machine."""
    print("Running command:", command)
    try:
        output = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, text=True
        )
        return f"Command executed:\n{output}"
    except subprocess.CalledProcessError as e:
        return f"Error:\n{e.output}"


@tool
def open_google_chrome(url: str) -> str:
    """
    Open Google Chrome with the specified URL.

    Parameters:
    - url (str): The URL to open in Google Chrome. (new_window:<url> opens the url in new window)
    """
    # Check if the URL contains the "new_window:" prefix
    new_window = False
    if url.startswith("new_window:"):
        new_window = True
        url = url[len("new_window:") :]

    if url:
        command = f"google-chrome-stable {'--new-window' if new_window else ''} {url}"
    else:
        command = "google-chrome-stable"

    try:
        subprocess.Popen(command, shell=True)
        return f"Google Chrome opened with URL: {url}"
    except Exception as e:
        return f"Error opening Google Chrome: {e}"


@tool
def open_whatsapp_web() -> str:
    """
    Open WhatsApp Web.
    """
    # os.system("gtk-launch ~/.local/share/applications/chrome-hnpfjngllnobngcgfapefoaidbinmjnm-Default.desktop")
    subprocess.Popen(["gtk-launch", "chrome-hnpfjngllnobngcgfapefoaidbinmjnm-Default.desktop"])


@tool
def do_nothing() -> None:
    """
    A function that does nothing.
    """
    print("Doing nothing...")
    return None