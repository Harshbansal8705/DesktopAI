# assistant.py
from dotenv import load_dotenv
from generate_prompt import prompt
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.messages import HumanMessage
from llm import model
from logger import setup_logger
from tools import (
    run_command,
    open_google_chrome,
    open_whatsapp_web,
    do_nothing,
    show_logs_widget,
    hide_logs_widget,
)
from langgraph.checkpoint.sqlite import SqliteSaver
import os, sqlite3

load_dotenv()

logger = setup_logger("assistant", "logs/assistant.log", level=os.environ["LOG_LEVEL"])

conn = sqlite3.connect("checkpoints/sqlite.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)


class State(AgentState):
    summary: str


logger.info("Chat model initialized.")


agent = create_react_agent(
    model=model,
    tools=[
        run_command,
        open_google_chrome,
        open_whatsapp_web,
        do_nothing,
        show_logs_widget,
        hide_logs_widget,
    ],
    prompt=prompt,
    state_schema=State,
    checkpointer=checkpointer,
)

logger.info("Agent initialized.")


if __name__ == "__main__":
    # Run the agent
    message = HumanMessage(content="Hey, how are you doing?")

    response = agent.invoke(
        {"messages": [message]},
        config={"configurable": {"thread_id": "1"}},
    )

    print(response["messages"][-1].content)
