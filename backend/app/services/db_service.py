import os
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import settings

# A new service for Supabase
from supabase import create_client, Client

class PineconeService:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
        self.index_name = settings.PINECONE_INDEX_NAME

    def _get_vectorstore(self):
        return PineconeVectorStore(
            pinecone_api_key=settings.PINECONE_API_KEY,
            index_name=self.index_name,
            embedding=self.embedding_model,
            namespace="question"  # or your desired namespace
        )

    def get_retriever(self):
        return self._get_vectorstore().as_retriever()

class SupabaseService:
    def __init__(self):
        self.url: str = settings.SUPABASE_URL
        self.key: str = settings.SUPABASE_SERVICE_KEY
        self.supabase: Client = create_client(self.url, self.key)

    def get_client(self):
        return self.supabase

# Dependencies for FastAPI
def get_pinecone_service():
    return PineconeService()

def get_supabase_service():
    return SupabaseService()