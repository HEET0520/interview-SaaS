import os
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import settings

# Supabase client
from supabase import create_client, Client


# -----------------------------
# Pinecone Service
# -----------------------------
class PineconeService:
    def __init__(self, namespace: str = "question"):
        try:
            self.embedding_model = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
            self.index_name = settings.PINECONE_INDEX_NAME
            self.namespace = namespace
        except Exception as e:
            raise RuntimeError(f"Error initializing PineconeService: {e}")

    def _get_vectorstore(self):
        try:
            return PineconeVectorStore(
                pinecone_api_key=settings.PINECONE_API_KEY,
                index_name=self.index_name,
                embedding=self.embedding_model,
                namespace=self.namespace
            )
        except Exception as e:
            raise RuntimeError(f"Error creating PineconeVectorStore: {e}")

    def get_retriever(self):
        try:
            return self._get_vectorstore().as_retriever()
        except Exception as e:
            raise RuntimeError(f"Error getting Pinecone retriever: {e}")


# -----------------------------
# Supabase Service
# -----------------------------
class SupabaseService:
    def __init__(self):
        try:
            self.url: str = settings.SUPABASE_URL
            self.key: str = settings.SUPABASE_SERVICE_KEY
            self.supabase: Client = create_client(self.url, self.key)
        except Exception as e:
            raise RuntimeError(f"Error initializing Supabase client: {e}")

    def get_client(self):
        return self.supabase


# -----------------------------
# Singleton Instances
# -----------------------------
_pinecone_service: PineconeService | None = None
_supabase_service: SupabaseService | None = None


def get_pinecone_service(namespace: str = "question") -> PineconeService:
    global _pinecone_service
    if _pinecone_service is None or _pinecone_service.namespace != namespace:
        _pinecone_service = PineconeService(namespace=namespace)
    return _pinecone_service


def get_supabase_service() -> SupabaseService:
    global _supabase_service
    if _supabase_service is None:
        _supabase_service = SupabaseService()
    return _supabase_service
