# tools.py
import os, subprocess
from langchain.tools import tool
from logger import setup_logger
from widget import overlay

logger = setup_logger("tools", "logs/tools.log", level=os.environ["LOG_LEVEL"])



@tool
def run_command(command: str) -> str:
    """Run a shell command on the local Linux machine."""
    logger.info(f"Executing command: {command}")
    try:
        output = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, text=True
        )
        logger.debug(f"[run_command] Output:\n{output}")
        return f"Command executed:\n{output}"
    except subprocess.CalledProcessError as e:
        logger.error(f"[run_command] Error:\n{e}")
        return f"Error:\n{e}"
    except Exception as e:
        logger.error(f"[run_command] Unexpected error: {e}")
        return f"Unexpected error:\n{e}"


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

    command = f"google-chrome-stable {'--new-window' if new_window else ''} {url if url else ''}"
    logger.info(f"[open_google_chrome] Command: {command}")

    try:
        subprocess.Popen(command, shell=True)
        return f"Google Chrome opened with URL: {url}"
    except Exception as e:
        logger.error(f"[open_google_chrome] Error: {e}")
        return f"Error opening Google Chrome: {e}"


@tool
def open_whatsapp_web() -> str:
    """
    Open WhatsApp Web
    """
    logger.info("[open_whatsapp_web] Opening WhatsApp Web...")
    try:
        subprocess.Popen(
            ["gtk-launch", "chrome-hnpfjngllnobngcgfapefoaidbinmjnm-Default.desktop"]
        )
        return "WhatsApp Web launched."
    except Exception as e:
        logger.error(f"[open_whatsapp_web] Error: {e}")
        return f"Error: {e}"


@tool
def show_logs_widget() -> str:
    """
    Show the logs widget
    """
    overlay.show()
    return "Logs widget opened."


@tool
def hide_logs_widget() -> str:
    """
    Hide the logs widget
    """
    overlay.hide()
    return "Logs widget closed."


@tool
def do_nothing() -> None:
    """
    A function that does nothing
    """
    logger.info("[do_nothing] Called.")
    return None
