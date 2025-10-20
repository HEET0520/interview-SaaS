from fastapi import FastAPI
from app.routers import chat_router, resume_router

app = FastAPI(title="Modular AI Interviewer Backend")

app.include_router(chat_router.router, prefix="/api/v1/chat")
app.include_router(resume_router.router, prefix="/api/v1/resume")
