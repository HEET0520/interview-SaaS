# backend/app/main.py
"""
FastAPI application entrypoint.
Provides:
- /upload_resume [POST]
- /interviews/new [POST]
- /interviews/history [GET]
- /interviews/{id} [GET]
- /ws/interview/{id} [WebSocket]

Important:
- This file uses get_current_user dependency to authenticate requests.
- WebSocket endpoint accepts either a Clerk JWT via query parameter `token` or `x_clerk_user_id` (dev).
  Because browsers cannot set custom headers during the WS handshake reliably, the frontend should
  connect with either: ws://.../ws/interview/{id}?token=<bearer_token>  (preferred) or
  ws://.../ws/interview/{id}?x_clerk_user_id=<clerk_id>  (dev fallback).
"""

import os
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from .auth import get_current_user, verify_clerk_jwt
from .resume_parser import save_resume
from .db_helpers import create_interview, get_interview_history, get_interview_with_transcript
from .supabase_client import supabase
from .websocket_handlers import handle_interview_websocket
import uvicorn

app = FastAPI(title="Interview SaaS Backend")

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Upload resume PDF -> parse -> store content in Supabase resumes table.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
    contents = await file.read()
    try:
        record = save_resume(clerk_user_id=current_user["clerk_user_id"], filename=file.filename, pdf_bytes=contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse or store resume: {e}")
    return {"status": "ok", "resume": record}


@app.post("/interviews/new")
async def new_interview(payload: dict, current_user: dict = Depends(get_current_user)):
    """
    Create a new interview session.
    payload must include: mode, role, difficulty, experience_level. resume_id optional.
    """
    required = ["mode", "role", "difficulty", "experience_level"]
    for r in required:
        if r not in payload:
            raise HTTPException(status_code=400, detail=f"Missing {r}")
    resume_id = payload.get("resume_id")
    interview = create_interview(clerk_user_id=current_user["clerk_user_id"], mode=payload["mode"], role=payload["role"],
                                 difficulty=payload["difficulty"], experience_level=payload["experience_level"], resume_id=resume_id)
    return {"status": "ok", "interview": interview}


@app.get("/interviews/history")
async def interviews_history(current_user: dict = Depends(get_current_user)):
    try:
        items = get_interview_history(current_user["clerk_user_id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok", "interviews": items}


@app.get("/interviews/{interview_id}")
async def interview_detail(interview_id: str, current_user: dict = Depends(get_current_user)):
    try:
        data = get_interview_with_transcript(interview_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    if data["interview"]["clerk_user_id"] != current_user["clerk_user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")
    return {"status": "ok", **data}


@app.websocket("/ws/interview/{interview_id}")
async def websocket_endpoint(websocket: WebSocket, interview_id: str, token: Optional[str] = Query(None), x_clerk_user_id: Optional[str] = Query(None)):
    """
    WebSocket handshake expects either:
      ws://.../ws/interview/{id}?token=<Bearer token>   (preferred)
    or  ws://.../ws/interview/{id}?x_clerk_user_id=<id>   (dev fallback)
    """
    # Accept connection first (so we can send close reason if needed)
    await websocket.accept()

    # Validate token or clerk_user_id
    clerk_user_id = None
    if token:
        # token may include "Bearer " prefix or only the token — accept both
        try:
            payload = verify_clerk_jwt(token)
        except Exception as e:
            await websocket.send_json({"type": "error", "text": f"Auth failed: {e}"})
            await websocket.close(code=1008)
            return
        clerk_user_id = payload.get("sub") or payload.get("user_id") or payload.get("uid")
        if not clerk_user_id:
            await websocket.send_json({"type": "error", "text": "Token missing subject claim"})
            await websocket.close(code=1008)
            return
    elif x_clerk_user_id:
        clerk_user_id = x_clerk_user_id
    else:
        await websocket.send_json({"type": "error", "text": "Missing authentication (token or x_clerk_user_id)"})
        await websocket.close(code=1008)
        return

    # Fetch interview meta and verify ownership
    resp = supabase.table("interviews").select("*").eq("id", interview_id).execute()
    if resp.status_code != 200 or not resp.data:
        await websocket.send_json({"type": "error", "text": "Interview not found"})
        await websocket.close(code=1003)
        return
    interview = resp.data[0]
    if interview["clerk_user_id"] != clerk_user_id:
        await websocket.send_json({"type": "error", "text": "Not allowed"})
        await websocket.close(code=1008)
        return

    # Fetch resume text if applicable
    resume_text = None
    if interview.get("resume_id"):
        r = supabase.table("resumes").select("*").eq("id", interview["resume_id"]).execute()
        if r.status_code == 200 and r.data:
            resume_text = r.data[0].get("content")

    # Delegate to handler
    try:
        await handle_interview_websocket(websocket, interview_meta=interview, resume_text=resume_text)
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "text": f"Server error: {e}"})
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
