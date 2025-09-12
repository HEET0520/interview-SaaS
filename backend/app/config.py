from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Loads and validates settings from the .env file.
    """
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    PINECONE_API_KEY: str
    GEMINI_API_KEY: str
    FIRECRAWL_API_KEY: str

    class Config:
        env_file = ".env"

# Create a single settings instance to be used throughout the application
settings = Settings()