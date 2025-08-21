# backend/app/websocket_handlers.py
"""
Robust WebSocket interview handler with streaming LLM output.

Design decisions:
- Use a background thread to run the blocking SDK streaming generator (stream_generate)
  and push textual chunks into an asyncio.Queue.
- The async websocket handler consumes from that queue and forwards to the client immediately.
- Concurrently, it listens for client messages (user answers / end).
- On disconnect or errors, background thread is signaled to stop via a sentinel and the queue is drained.
- Each question is appended to transcripts in Supabase; user answers likewise.
"""

import asyncio
import threading
import uuid
import time
from typing import Optional
from fastapi import WebSocket
from .llm_gemini import generate_question_role_based, generate_question_resume_based, stream_generate, analyze_transcript
from .db_helpers import append_transcript, finalize_analysis
from .supabase_client import supabase

# sentinel to indicate stream end
_STREAM_END = object()


def _start_stream_thread(model: str, prompt: str, out_queue: asyncio.Queue, stop_event: threading.Event):
    """
    Run in background thread: iterate the blocking stream_generate generator,
    put chunks into the asyncio queue. Respect stop_event to abort early.
    """
    try:
        for chunk in stream_generate(model, prompt):
            if stop_event.is_set():
                break
            # put chunk into queue (use asyncio.run to schedule put if loop not accessible)
            # We'll use asyncio.get_event_loop().call_soon_threadsafe to schedule queue.put_nowait
            try:
                asyncio.get_event_loop().call_soon_threadsafe(out_queue.put_nowait, chunk)
            except RuntimeError:
                # No running loop in this thread's context; use alternative:
                loop = asyncio.new_event_loop()
                loop.call_soon_threadsafe(out_queue.put_nowait, chunk)
            # small sleep to be polite
            time.sleep(0.01)
    except Exception as e:
        # Send error into queue so websocket can report it
        try:
            asyncio.get_event_loop().call_soon_threadsafe(out_queue.put_nowait, f"[stream error] {e}")
        except Exception:
            pass
    finally:
        # signal end
        try:
            asyncio.get_event_loop().call_soon_threadsafe(out_queue.put_nowait, _STREAM_END)
        except Exception:
            pass


async def handle_interview_websocket(websocket: WebSocket, interview_meta: dict, resume_text: Optional[str] = None):
    """
    websocket: connected websocket (already accepted)
    interview_meta: contains id, mode, role, difficulty, experience_level, clerk_user_id
    resume_text: optional resume content string
    """
    interview_id = interview_meta["id"]
    clerk_user_id = interview_meta["clerk_user_id"]

    #
    # Helper: send JSON safely catching exceptions
    #
    async def safe_send(payload):
        try:
            await websocket.send_json(payload)
        except Exception:
            # connection may be closed or broken; raise to outer scope
            raise

    await safe_send({"type": "info", "text": f"Starting interview ({interview_meta['mode']}) — role: {interview_meta['role']}"})

    # QUESTION / ANSWER loop
    transcripts_text_for_analysis = []  # keep small transcript in memory for analysis
    stop = False

    try:
        # Generate first question (streaming)
        if interview_meta["mode"] == "role":
            prompt = generate_question_role_based(interview_meta["role"], interview_meta["difficulty"], interview_meta["experience_level"])
            model = None  # we used generate_question_role_based non-streaming for first draft
            # But for streaming UX, prefer stream_generate with role model
            model = ( "gemini-1.5-flash" )
            # Build a streaming prompt from template
            full_prompt = prompt  # non-streaming path will also work
        else:
            # resume based
            prompt = generate_question_resume_based(interview_meta["role"], interview_meta["difficulty"], interview_meta["experience_level"], resume_text or "")
            model = ( "gemini-1.5-pro" )
            full_prompt = prompt

        # Store the AI question (full text)
        append_transcript(interview_id=interview_id, actor="ai", text=prompt)
        transcripts_text_for_analysis.append(f"AI: {prompt}\n")

        # Now stream the question to the client using the robust streamer
        # Create asyncio.Queue and a threading.Event to stop thread
        queue = asyncio.Queue()
        stop_event = threading.Event()

        # Start background thread to push stream chunks into queue
        thread = threading.Thread(target=_start_stream_thread, args=(model, full_prompt, queue, stop_event), daemon=True)
        thread.start()

        # Consumer loop: concurrently read from ws and queue
        async def ws_receiver(queue_in):
            """
            Receives messages from client. Returns when interview ends (client sends {"type":"end"}).
            """
            while True:
                try:
                    data = await websocket.receive_json()
                except Exception:
                    # Client disconnected
                    return {"type": "disconnect"}
                if data.get("type") == "answer":
                    user_text = data.get("text", "")
                    append_transcript(interview_id=interview_id, actor="user", text=user_text)
                    transcripts_text_for_analysis.append(f"User: {user_text}\n")
                    # once answer received, generate next question (we'll start new stream)
                    # Put a marker into queue to indicate we should start next question
                    await queue_in.put({"__incoming_answer__": user_text})
                elif data.get("type") == "end":
                    return {"type": "end"}
                else:
                    # ignore unknown
                    await queue_in.put({"__info__": data})
            # unreachable
            return {"type": "finished"}

        # We'll run ws_receiver as a task
        recv_task = asyncio.create_task(ws_receiver(queue))

        # Outgoing: forward chunks from queue to client; if we receive special markers, handle them
        while True:
            item = await queue.get()
            if item is _STREAM_END:
                # stream finished for current question
                await safe_send({"type": "question_end"})
                # check whether ws_receiver has any messages queued (answers) immediately
                # Wait briefly for any incoming answer event placed into queue
                # Peek at queue without consuming? Not available; use small sleep and continue
                # If recv_task finished, break
                if recv_task.done():
                    res = recv_task.result()
                    if res.get("type") == "end":
                        # Prepare final analysis
                        await safe_send({"type": "info", "text": "Interview finished, generating analysis..."})
                        full_transcript = "\n".join(transcripts_text_for_analysis)
                        analysis = analyze_transcript(full_transcript)
                        finalize_analysis(interview_id=interview_id, analysis=analysis)
                        await safe_send({"type": "end", "analysis": analysis})
                        stop_event.set()
                        break
                    elif res.get("type") == "disconnect":
                        # client disconnected
                        stop_event.set()
                        break
                # else continue loop and wait for next events (answers will be injected into queue by ws_receiver)
            elif isinstance(item, dict) and item.get("__incoming_answer__"):
                # An answer was received; generate next question (stream)
                user_text = item["__incoming_answer__"]
                # Generate next question synchronously (best-effort). Choose mode.
                if interview_meta["mode"] == "role":
                    next_prompt = generate_question_role_based(interview_meta["role"], interview_meta["difficulty"], interview_meta["experience_level"])
                    next_model = "gemini-1.5-flash"
                else:
                    next_prompt = generate_question_resume_based(interview_meta["role"], interview_meta["difficulty"], interview_meta["experience_level"], resume_text or "")
                    next_model = "gemini-1.5-pro"

                append_transcript(interview_id=interview_id, actor="ai", text=next_prompt)
                transcripts_text_for_analysis.append(f"AI: {next_prompt}\n")
                # restart stream thread for next question
                # Stop previous thread if it exists
                # start a fresh thread that streams next_prompt into queue
                stop_event = threading.Event()
                thread = threading.Thread(target=_start_stream_thread, args=(next_model, next_prompt, queue, stop_event), daemon=True)
                thread.start()
            elif isinstance(item, dict) and item.get("__info__"):
                # forward info to client
                await safe_send({"type": "info", "text": str(item.get("__info__"))})
            else:
                # Regular text chunk from LLM; forward to client
                text = item
                # For long chunks, we may split them to keep messages small
                chunk_size = 800
                for i in range(0, len(text), chunk_size):
                    await safe_send({"type": "question", "text": text[i:i+chunk_size]})
        # end while
    except Exception as e:
        try:
            await safe_send({"type": "error", "text": f"Server error: {e}"})
        except Exception:
            pass
    finally:
        # ensure background thread and queue are cleaned up
        try:
            stop_event.set()
        except Exception:
            pass
        try:
            if not recv_task.done():
                recv_task.cancel()
        except Exception:
            pass
        try:
            await websocket.close()
        except Exception:
            pass
