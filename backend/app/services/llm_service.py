import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

def get_llm():
    os.environ["GOOGLE_API_KEY"] = settings.GEMINI_API_KEY
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL, 
        temperature=0.7
    )