import functools, subprocess
from typing import Literal, Optional
from langchain_core.tools import tool as _tool
from langchain_tavily import TavilySearch
from src.config import config
from src.utils.logger import get_logger
from src.ui.overlay import overlay
from PIL import ImageGrab

logger = get_logger()

_stop_assistant = False


def register_stop_assistant(callback):
    global _stop_assistant
    _stop_assistant = callback


def tool(_func=None, *, return_direct=False):
    """
    A Tool decorator with logging.
    """
    def decorator(func):
        @_tool(return_direct=return_direct)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger.info(f"[{func.__name__}] Called with args: {args}, kwargs: {kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"[{func.__name__}] Result: {result}")
                return result
            except Exception as e:
                logger.error(f"[{func.__name__}] Error: {e}")
                return f"Error in {func.__name__}: {e}"
        return wrapper
    return decorator(_func) if _func is not None else decorator


@tool
def run_command(command: str) -> str:
    """Run a shell command on the local Linux machine."""
    return subprocess.check_output(
        command, shell=True, stderr=subprocess.STDOUT, text=True
    )


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
def show_popup_widget() -> str:
    """
    Show the popup widget
    """
    overlay.show()
    return "Popup widget opened."


@tool
def hide_popup_widget() -> str:
    """
    Hide the popup widget
    """
    overlay.hide()
    return "Popup widget closed."


@tool
def do_nothing() -> None:
    """
    A function that does nothing
    """
    logger.info("[do_nothing] Called.")
    return None


@tool(return_direct=True)
def get_screenshot() -> str:
    """
    Get a screenshot of the current screen
    """
    logger.info("[get_screenshot] Taking screenshot...")
    screenshot = ImageGrab.grab()
    screenshot.save(config.SCREENSHOT_FILE)

    return f"tool_message:get_screenshot:{config.SCREENSHOT_FILE}"


@tool(return_direct=True)
def exit_assistant() -> str:
    """
    Exit / Stop / Shutdown
    """
    if _stop_assistant:
        # Schedule the shutdown to happen after the response is returned
        import threading
        threading.Timer(0.1, _stop_assistant).start()
    else:
        logger.warning("[exit] No stop callback registered.")
        return "No stop callback registered."
    return "Assistant stopped."


@tool
def web_search(
    query: str,
    max_results: int = 5,
    search_depth: Optional[Literal["basic", "advanced"]] = "basic"
) -> str:
    """
    Execute a search query using the Tavily Search API.

    Parameters:
    - query (str): The search query to execute.
    - max_results (int): The maximum number of results to return. Default is 5.
    - search_depth (Optional[Literal["basic", "advanced"]]): The depth of the search.
    Default is "basic". Use "advanced" for more detailed results.
    """
    search_tool = TavilySearch(api_key=config.TAVILY_API_KEY, max_results=max_results, search_depth=search_depth)
    try:
        results = search_tool.invoke({"query": query})
        return str(results)
    except Exception as e:
        logger.error(f"[web_search] Error: {e}")
        return f"Error during web search: {e}"


@tool
def mirror_mobile_screen() -> str:
    """
    Mirror the mobile screen using scrcpy.
    """
    subprocess.Popen("scrcpy", shell=True)
    return "Starting mobile screen mirroring using scrcpy."


@tool
def mirror_mobile_camera(facing: Literal["front", "back"] = "back") -> str:
    """
    Mirror the mobile camera using scrcpy.
    """
    subprocess.Popen([
        "scrcpy",
        "--video-source=camera",
        f"--camera-facing={facing}"
    ])
    return "Starting mobile camera mirroring using scrcpy."
