import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    base_url=os.getenv("GEMINI_API_BASE_URL"),
    api_key=os.getenv("GEMINI_API_KEY")
)
ollama_client = AsyncOpenAI(
    base_url=os.getenv("OLLAMA_API_BASE_URL"),
    api_key=os.getenv("API_KEY")
)