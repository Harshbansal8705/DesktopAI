from langchain.chat_models import init_chat_model
from config import config

model = init_chat_model(
    "groq:meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0.8,
    api_key=config.GROQ_API_KEY,
)
