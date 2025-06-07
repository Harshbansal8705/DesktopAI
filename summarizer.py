from langchain_core.messages import HumanMessage
from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from llm import model


def summarize_conversation(state: AgentState, max_tokens: int = 1000):
    summary = state.get("summary", "")
    messages = state.get("messages", [])
    if len(messages) < 4:
        return {"summary": summary, "messages": messages}

    recent_messages = trim_messages(
        messages=messages,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=max_tokens,
        start_on="human",
        end_on=("human", "tool"),
        include_system=True,
        allow_partial=False,
    )

    if len(recent_messages) <= 4:
        kept_ids = {m.id for m in messages[-4:] if hasattr(m, "id")}
    else:
        kept_ids = {m.id for m in recent_messages if hasattr(m, "id")}
    old_messages = [m for m in messages if hasattr(m, "id") and m.id not in kept_ids]

    if not old_messages:
        return {"summary": summary, "messages": messages}

    if summary:
        prompt = (
            f"This is a summary of the conversation so far:\n{summary}\n\n"
            "Extend the summary by including the content of the new messages above. (Don't include this instruction in the summary)"
        )
    else:
        prompt = "Create a summary of the conversation above (don't include this instruction in the summary):"

    summarization_input = old_messages + [HumanMessage(content=prompt)]
    response = model.invoke(summarization_input)

    return {
        "summary": response.content,
        "messages": recent_messages
    }
