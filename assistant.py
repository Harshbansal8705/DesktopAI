# assistant.py
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AnyMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langmem.short_term import SummarizationNode
from typing import Any
from tools import run_command, open_google_chrome, open_whatsapp_web, do_nothing

load_dotenv()

checkpointer = InMemorySaver()

class State(AgentState):
    context: dict[str, Any]


def prompt(state: AgentState, config: RunnableConfig) -> list[AnyMessage]:
    user_name = config["configurable"].get("user_name")
    system_msg = f"You are a helpful assistant. Address the user as {user_name}."
    return [{"role": "system", "content": system_msg}] + state["messages"]


# model = ChatTogether(
#     model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
#     temperature=0.8,
#     api_key=os.environ.get("TOGETHER_API_KEY"),
# )

model = init_chat_model(
    "gemini-2.5-pro-exp-03-25",
    model_provider="google_genai",
    temperature=0.8,
    verbose=True
)

summarization_node = SummarizationNode(
    token_counter=count_tokens_approximately,
    model=model,
    max_tokens=384,
    max_summary_tokens=128,
    output_messages_key="llm_input_messages",
)

prompt = """You are Jarvis, an helpful AI assistant running locally on the user's Linux machine. You have to understand natural language and respond in a conversational manner. You also have access to various tools which you can use when required.

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

"""

agent = create_react_agent(
    model=model,
    tools=[run_command, open_google_chrome, open_whatsapp_web, do_nothing],
    prompt=prompt,
    pre_model_hook=summarization_node,
    state_schema=State,
    checkpointer=checkpointer,
)


if __name__ == "__main__":
    # Run the agent
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "Hello"}]},
        config={"configurable": {"user_name": "Harsh Bansal", "thread_id": "1"}},
    )

    print(response["messages"][-1].content)
