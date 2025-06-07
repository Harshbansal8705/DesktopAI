# assistant.py
import base64
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
    get_screenshot,
    show_logs_widget,
    hide_logs_widget,
    do_nothing,
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
        get_screenshot,
        show_logs_widget,
        hide_logs_widget,
        do_nothing,
    ],
    prompt=prompt,
    state_schema=State,
    checkpointer=checkpointer,
)

logger.info("Agent initialized.")


def call_agent(message):
    config = {"configurable": {"thread_id": "4"}}
    response = agent.invoke(
        {"messages": [message]},
        config=config,
    )
    msg = response["messages"][-1].content

    # Handle the case when response["messages"][-1].content is a list of messages
    if isinstance(msg, list):
        msg = "\n".join([msg.content for msg in msg])
    if msg.startswith("tool_message:"):
        tool_name = msg.split(":")[1]
        tool_args = msg.split(":")[2]
        print(tool_name, tool_args)
        if tool_name == "get_screenshot":
            with open(tool_args, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")

            response = agent.invoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{image_data}"
                                    },
                                }
                            ],
                        }
                    ]
                },
                config=config,
            )

            msg = response["messages"][-1].content

            # Handle the case when response["messages"][-1].content is a list of messages
            if isinstance(msg, list):
                msg = "\n".join([msg.content for msg in msg])
            return msg
        else:
            return msg
    else:
        return msg


if __name__ == "__main__":
    # Run the agent
    message = HumanMessage(content="Hey, how are you doing?")
    config = {"configurable": {"thread_id": "1"}}

    response = call_agent(message)

    print(response)
