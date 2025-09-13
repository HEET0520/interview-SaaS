from fastapi import APIRouter, Depends
from app.models.request_models import ChatRequest
from app.services.rag_service import RAGService

router = APIRouter()

# Dependency for FastAPI to get a RAGService instance
def get_rag_service():
    return RAGService()

@router.post("/chat")
async def chat(request: ChatRequest, rag_service: RAGService = Depends(get_rag_service)):
    response = await rag_service.get_response(
        role=request.role,
        tech_stack=request.tech_stack,
        difficulty=request.difficulty,
        session_id=request.session_id
    )
    return {"response": response}

@router.get("/")
def read_root():
    return {"message": "AI Interviewer Backend is running."}