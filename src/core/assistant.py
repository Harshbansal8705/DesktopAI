# assistant.py
import base64
import sqlite3
import threading

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState

from src.config import config
from src.core.llm import model
from src.utils.logger import get_logger

from .generate_prompt import prompt
from .tools import get_all_tools

logger = get_logger()

# Lazy-initialized agent — created on first call to call_agent() instead of
# at import time. This avoids opening a SQLite connection and downloading the
# silero-vad model when assistant.py is merely imported (e.g. during tests).
_agent = None
_agent_lock = threading.Lock()


def _get_agent():
    global _agent
    if _agent is not None:
        return _agent
    with _agent_lock:
        if _agent is not None:  # double-checked locking
            return _agent
        logger.info("Initializing agent and SQLite checkpointer...")
        conn = sqlite3.connect(config.CHECKPOINTS_DB, check_same_thread=False)
        checkpointer = SqliteSaver(conn)

        class State(AgentState):
            summary: str

        _agent = create_react_agent(
            model=model,
            tools=get_all_tools(),
            prompt=prompt,
            state_schema=State,
            checkpointer=checkpointer,
        )
        logger.info("Agent initialized.")
    return _agent


def call_agent(message):
    agent = _get_agent()
    config_dict = {"configurable": {"thread_id": config.THREAD_ID}}
    response = agent.invoke(
        {"messages": [message]},
        config_dict,
    )
    msg = response["messages"][-1].content

    # Handle the case when response["messages"][-1].content is a list of messages
    if isinstance(msg, list):
        msg = "\n".join([msg.content for msg in msg])
    if msg.startswith("tool_message:"):
        tool_name = msg.split(":")[1]
        tool_args = msg.split(":")[2]
        if tool_name == "get_screenshot":
            with open(tool_args, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            return f"tool_message:get_screenshot:{encoded_string}"
        return msg
    else:
        return msg


if __name__ == "__main__":
    # Run the agent
    message = HumanMessage(content="Hey, how are you doing?")
    response = call_agent(message)
    print(response)
