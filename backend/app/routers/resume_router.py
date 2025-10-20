from fastapi import APIRouter, UploadFile, File, HTTPException
import fitz  # PyMuPDF
from app.services.db_service import get_supabase_service

router = APIRouter()

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported")

    pdf_bytes = await file.read()
    doc = fitz.open("pdf", pdf_bytes)
    text = "\n".join([page.get_text() for page in doc])

    # Store in Supabase
    supabase = get_supabase_service().get_client()
    session_id = file.filename.split(".")[0]  # use filename as ID for now
    supabase.table("resumes").upsert({
        "session_id": session_id,
        "resume_text": text
    }).execute()

    return {"message": "Resume uploaded & parsed", "session_id": session_id}
