from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Loads and validates settings from the .env file.
    """
    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    # AI & Embedding Models
    PINECONE_API_KEY: str
    GEMINI_API_KEY: str
    HUGGINGFACEHUB_ACCESS_TOKEN: str
    FIRECRAWL_API_KEY: str 
    SERPAPI_API_KEY: str
    GROQ_API_KEY: str
    # Pinecone Index Configuration
    PINECONE_INDEX_NAME: str = "interview-questions"
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east-1"
    
    # Embedding Model Configuration
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_MODEL_PATH: str = "embedding/"

    # LLM Model Configuration
    GEMINI_MODEL: str = "gemini-2.5-flash"

    class Config:
        env_file = ".env"
        extra = "allow"

# Create a single settings instance to be used throughout the application
settings = Settings()