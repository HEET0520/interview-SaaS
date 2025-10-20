from fastapi import APIRouter, Depends
from app.models.request_models import ChatRequest
from app.services.rag_service import RAGService

router = APIRouter()

def get_rag_service():
    return RAGService()

@router.post("/")
async def chat(request: ChatRequest, rag_service: RAGService = Depends(get_rag_service)):
    response = await rag_service.get_response(
        role=request.role,
        tech_stack=request.tech_stack,
        difficulty=request.difficulty,
        session_id=request.session_id,
        answer=request.answer   # pass candidate answer if provided
    )
    return {"response": response}
