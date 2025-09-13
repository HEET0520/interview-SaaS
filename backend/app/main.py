from fastapi import FastAPI
from app.routers import chat_router

app = FastAPI(title="Modular AI Interviewer Backend")

# Include the router for your chat functionality
app.include_router(chat_router.router, prefix="/api/v1")