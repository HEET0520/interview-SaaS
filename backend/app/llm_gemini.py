# backend/app/llm_gemini.py
"""
Gemini adapter using google-generativeai (google-generativeai package).
- Provides:
    - generate_question_role_based(...)
    - generate_question_resume_based(...)
    - stream_generate(...) -> generator of text chunks
    - analyze_transcript(...)

Design:
- Uses Client.models.generate_content for single-shot calls.
- Uses Client.models.generate_content_stream for streaming.
- If the SDK or API key is missing, uses a safe stub fallback.
"""

import os
import json
import re
from pathlib import Path
from typing import Iterable, Optional

try:
    import google.generativeai as genai  # google-generativeai
    SDK_AVAILABLE = True
except Exception:
    SDK_AVAILABLE = False

TEMPLATES_DIR = Path(__file__).parent / "prompts"
ROLE_TEMPLATE = (TEMPLATES_DIR / "role_only_prompt.txt").read_text(encoding="utf-8")
RESUME_TEMPLATE = (TEMPLATES_DIR / "resume_based_prompt.txt").read_text(encoding="utf-8")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_ROLE = os.getenv("GEMINI_MODEL_ROLE", "gemini-1.5-flash")
GEMINI_MODEL_RESUME = os.getenv("GEMINI_MODEL_RESUME", "gemini-1.5-pro")

# Configure SDK if possible
if SDK_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        # Some versions of the SDK pick keys from env automatically; ignore failures
        pass


def _stub_response(prompt: str, model: str) -> str:
    role_hint = "software developer"
    if "Role:" in prompt:
        try:
            role_hint = prompt.split("Role:")[1].splitlines()[0].strip()
        except Exception:
            pass
    return f"(stub {model}) For the role of {role_hint}: Briefly describe a recent project where you optimized performance and tradeoffs."

def _extract_text(resp) -> str:
    # best-effort extraction from SDK response object
    if resp is None:
        return ""
    if hasattr(resp, "text") and resp.text:
        return resp.text
    try:
        if hasattr(resp, "candidates") and resp.candidates:
            c0 = resp.candidates[0]
            if hasattr(c0, "content"):
                content = c0.content
                if isinstance(content, (list, tuple)):
                    pieces = []
                    for piece in content:
                        if isinstance(piece, dict):
                            pieces.append(piece.get("text", ""))
                        elif hasattr(piece, "text"):
                            pieces.append(getattr(piece, "text", ""))
                        else:
                            pieces.append(str(piece))
                    return " ".join(pieces).strip()
            if hasattr(c0, "text"):
                return c0.text
    except Exception:
        pass
    try:
        return json.dumps(resp.__dict__)
    except Exception:
        return str(resp)


def _generate_once(model: str, prompt: str, max_output_tokens: int = 400) -> str:
    """Single-shot generation"""
    if not (SDK_AVAILABLE and GEMINI_API_KEY):
        return _stub_response(prompt, model)
    try:
        client = genai.Client()
        response = client.models.generate_content(
            model=model,
            contents=[prompt],
            max_output_tokens=max_output_tokens,
            temperature=0.2
        )
        return _extract_text(response)
    except Exception as e:
        return _stub_response(prompt + f"\n\n[error: {e}]", model)


def generate_question_role_based(role: str, difficulty: str, experience: str) -> str:
    prompt = ROLE_TEMPLATE.replace("{{ROLE}}", role).replace("{{DIFFICULTY}}", difficulty).replace("{{EXPERIENCE}}", experience)
    return _generate_once(GEMINI_MODEL_ROLE, prompt)


def generate_question_resume_based(role: str, difficulty: str, experience: str, resume_text: str) -> str:
    prompt = RESUME_TEMPLATE.replace("{{ROLE}}", role).replace("{{DIFFICULTY}}", difficulty).replace("{{EXPERIENCE}}", experience).replace("{{RESUME}}", resume_text)
    return _generate_once(GEMINI_MODEL_RESUME, prompt)


def stream_generate(model: str, prompt: str, max_output_tokens: int = 400) -> Iterable[str]:
    """
    Stream generator of text chunks.
    Yields strings as they are produced by the SDK. If SDK not available, yields single stub.
    """
    if not (SDK_AVAILABLE and GEMINI_API_KEY):
        yield _stub_response(prompt, model)
        return

    try:
        client = genai.Client()
        # SDK supports streaming via generate_content_stream
        stream = client.models.generate_content_stream(
            model=model,
            contents=[prompt],
            max_output_tokens=max_output_tokens,
            temperature=0.2
        )
        # iterate events
        for event in stream:
            # event may have .text or .delta or .content
            text = ""
            if hasattr(event, "text") and event.text:
                text = event.text
            elif hasattr(event, "delta") and event.delta:
                text = event.delta
            elif hasattr(event, "content") and event.content:
                # content might be a dict or list
                try:
                    if isinstance(event.content, (list, tuple)):
                        # collect text pieces
                        pieces = []
                        for c in event.content:
                            if isinstance(c, dict):
                                pieces.append(c.get("text", ""))
                            elif hasattr(c, "text"):
                                pieces.append(getattr(c, "text", ""))
                            else:
                                pieces.append(str(c))
                        text = " ".join(pieces)
                    else:
                        text = str(event.content)
                except Exception:
                    text = str(event.content)
            else:
                # fallback
                text = str(event)
            if text:
                yield text
        return
    except Exception as e:
        # fallback
        yield _generate_once(model, prompt)


def analyze_transcript(transcript: str) -> dict:
    analysis_prompt = f"""
You are a helpful coach. Given the following interview transcript, produce a JSON with keys:
- strengths: short list
- weaknesses: short list
- improvements: suggestions
- resources: recommended learning resources (URLs or short names)

Transcript:
{transcript}

Return strictly valid JSON only.
"""
    raw = _generate_once(GEMINI_MODEL_RESUME, analysis_prompt, max_output_tokens=800)
    try:
        parsed = json.loads(raw)
    except Exception:
        m = re.search(r"(\{.*\})", raw, re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(1))
            except Exception:
                parsed = {
                    "strengths": [],
                    "weaknesses": [],
                    "improvements": raw[:400],
                    "resources": []
                }
        else:
            parsed = {
                "strengths": [],
                "weaknesses": [],
                "improvements": raw[:400],
                "resources": []
            }
    parsed.setdefault("strengths", parsed.get("strengths") or [])
    parsed.setdefault("weaknesses", parsed.get("weaknesses") or [])
    parsed.setdefault("improvements", parsed.get("improvements") or "")
    parsed.setdefault("resources", parsed.get("resources") or [])
    return parsed
