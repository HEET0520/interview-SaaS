from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    role: str
    tech_stack: List[str]
    difficulty: str = "Beginner"
    session_id: str
    answer: Optional[str] = None  # NEW
