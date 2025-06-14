from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import os

load_dotenv()

model = init_chat_model(
    "groq:meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.8,
    api_key=os.environ["GROQ_API_KEY"],
)
