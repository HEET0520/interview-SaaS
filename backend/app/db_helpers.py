# backend/app/db_helpers.py
"""
Helpers for interacting with Supabase tables: interviews, transcripts, analysis_reports, resumes.
"""

from typing import Dict, Any, List, Optional
from .supabase_client import supabase
from datetime import datetime
import uuid


def create_interview(clerk_user_id: str, mode: str, role: str, difficulty: str, experience_level: str, resume_id: Optional[str] = None) -> Dict[str, Any]:
    session_id = str(uuid.uuid4())
    payload = {
        "id": session_id,
        "clerk_user_id": clerk_user_id,
        "mode": mode,
        "role": role,
        "difficulty": difficulty,
        "experience_level": experience_level,
        "resume_id": resume_id,
        "created_at": datetime.utcnow().isoformat()
    }
    resp = supabase.table("interviews").insert(payload).execute()
    if resp.status_code not in (200, 201):
        raise Exception(f"Failed to create interview: {resp.error}")
    return payload


def append_transcript(interview_id: str, actor: str, text: str) -> None:
    payload = {
        "id": str(uuid.uuid4()),
        "interview_id": interview_id,
        "actor": actor,  # "ai" or "user"
        "text": text,
        "created_at": datetime.utcnow().isoformat()
    }
    resp = supabase.table("transcripts").insert(payload).execute()
    if resp.status_code not in (200, 201):
        raise Exception(f"Failed to append transcript: {resp.error}")


def finalize_analysis(interview_id: str, analysis: Dict[str, Any]) -> None:
    payload = {
        "id": str(uuid.uuid4()),
        "interview_id": interview_id,
        "strengths": analysis.get("strengths"),
        "weaknesses": analysis.get("weaknesses"),
        "improvements": analysis.get("improvements"),
        "resources": analysis.get("resources"),
        "created_at": datetime.utcnow().isoformat()
    }
    resp = supabase.table("analysis_reports").insert(payload).execute()
    if resp.status_code not in (200, 201):
        raise Exception(f"Failed to save analysis report: {resp.error}")


def get_interview_history(clerk_user_id: str) -> List[Dict[str, Any]]:
    resp = supabase.table("interviews").select("*").eq("clerk_user_id", clerk_user_id).order("created_at", desc=True).execute()
    if resp.status_code != 200:
        raise Exception("Failed to fetch interviews")
    return resp.data


def get_interview_with_transcript(interview_id: str) -> Dict[str, Any]:
    resp = supabase.table("interviews").select("*").eq("id", interview_id).execute()
    if resp.status_code != 200 or not resp.data:
        raise Exception("Interview not found")
    interview = resp.data[0]

    t_resp = supabase.table("transcripts").select("*").eq("interview_id", interview_id).order("created_at", asc=True).execute()
    transcripts = t_resp.data if t_resp.status_code == 200 else []

    a_resp = supabase.table("analysis_reports").select("*").eq("interview_id", interview_id).order("created_at", desc=True).execute()
    analysis = a_resp.data[0] if a_resp.status_code == 200 and a_resp.data else None

    return {"interview": interview, "transcripts": transcripts, "analysis": analysis}
