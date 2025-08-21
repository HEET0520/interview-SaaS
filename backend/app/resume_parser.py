# backend/app/resume_parser.py
"""
Resume parsing using PyMuPDF (fitz). For scanned PDFs, optional OCR via pytesseract.
Stores the text into Supabase resumes table.
"""

import fitz  # PyMuPDF
from typing import Tuple
import os
from .supabase_client import supabase
from uuid import uuid4
from datetime import datetime

# Optional: tesseract if you want OCR for scanned PDFs (not enabled by default)
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    text_parts = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            text = page.get_text().strip()
            if text:
                text_parts.append(text)
            else:
                # if page has no text, and OCR available, render to image and OCR
                if OCR_AVAILABLE:
                    pix = page.get_pixmap(dpi=200, alpha=False)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = pytesseract.image_to_string(img)
                    if ocr_text:
                        text_parts.append(ocr_text)
        doc.close()
    except Exception as e:
        raise e
    return "\n\n".join(text_parts)


def save_resume(clerk_user_id: str, filename: str, pdf_bytes: bytes) -> dict:
    text = extract_text_from_pdf_bytes(pdf_bytes)
    resume_id = str(uuid4())
    record = {
        "id": resume_id,
        "clerk_user_id": clerk_user_id,
        "filename": filename,
        "content": text,
        "created_at": datetime.utcnow().isoformat()
    }
    resp = supabase.table("resumes").insert(record).execute()
    if resp.status_code not in (200, 201):
        raise Exception("Failed to save resume")
    return record
