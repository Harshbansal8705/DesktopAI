from langchain.chat_models import init_chat_model
from src.config import config


model = init_chat_model(
    model=config.LLM_MODEL,
    model_provider=config.LLM_PROVIDER,
    temperature=config.LLM_TEMPERATURE,
    api_key=config.LLM_API_KEY,
)
