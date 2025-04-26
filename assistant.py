# assistant.py
from dotenv import load_dotenv
from langchain_together import ChatTogether
from langchain.agents import initialize_agent, AgentType
from tools import run_command, open_google_chrome
from langchain.memory import ConversationBufferMemory
import os

load_dotenv()

# Create memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Load Together model (LLaMA-3)
llm = ChatTogether(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    temperature=0.8,
    together_api_key=os.environ["TOGETHER_API_KEY"]
)

# Define tools
tools = [run_command, open_google_chrome]

# Create agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
)
