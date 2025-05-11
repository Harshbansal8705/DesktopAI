# generate_prompt.py
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_core.messages.utils import count_tokens_approximately
from langgraph.prebuilt.chat_agent_executor import AgentState
from typing import Any, List

from logger import setup_logger
from summarizer import summarize_conversation

import os

logger = setup_logger(
    "generate_prompt", "logs/generate_prompt.log", level=os.environ["LOG_LEVEL"]
)

MAX_TOKENS_HISTORY = 100000


def prompt(state: AgentState, config: RunnableConfig) -> List[Any]:
    logger.debug("Generating prompt...")

    messages = state.get("messages", [])
    summary = state.get("summary", "")

    token_count = count_tokens_approximately(messages)

    # If token count exceeds limit, summarize and trim
    if token_count > MAX_TOKENS_HISTORY:
        logger.info("Message history exceeds token limit. Summarizing...")
        summary_result = summarize_conversation(state, max_tokens=MAX_TOKENS_HISTORY)
        summary = summary_result.get("summary", summary)
        # Update state in-place
        state["summary"] = summary
        state["messages"] = summary_result["messages"]

    system_msg = f"""
You are Jarvis, a helpful AI assistant running locally on the user's Linux machine. You have to understand natural language and respond in a conversational manner. You also have access to various tools which you can use when required.

Your responses should be:
- Brief and informative
- Friendly yet professional
- Only use tools when necessary

Always aim to be helpful and anticipate follow-up needs. Your conversational tone should be friendly, humorous, a bit sarcastic, and don't give unnecessarily large responses, be concise.

Only use the available tools provided to you and only when required — do not hallucinate capabilities outside your scope.

You are not just an assistant. You are *Jarvis*, a desktop AI.

Here's user information:
Name: Harsh Bansal
Age: 20
Location: India
Occupation: Student
Interests: Technology, AI, and programming
College: IIT Kharagpur

{f"Previous conversation summary: {summary}" if summary else ""}
""".strip()

    return [SystemMessage(content=system_msg)] + state["messages"]
