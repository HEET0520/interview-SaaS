from pydantic import BaseModel
from typing import List
class ChatRequest(BaseModel):
    role: str
    tech_stack: List[str]
    difficulty: str = "Beginner"  # optional filter
    session_id: str