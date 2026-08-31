"""
api.py — FastAPI backend for the AI Meeting Summarization Application.

Exposes two summarization endpoints for the security demo:
  POST /summarize/vulnerable  — no prompt isolation (intentionally weak)
  POST /summarize/secure      — validated, isolated, sanitized (mitigated)

Run: uvicorn api:app --reload --port 8000
Docs (auto-generated): http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

from config import (
    GROQ_API_KEY, GROQ_MODEL,
    VULNERABLE_SYSTEM_PROMPT, VULNERABLE_PROMPT_TEMPLATE,
    SECURE_SYSTEM_PROMPT, SECURE_PROMPT_TEMPLATE,
)
from utils import validate_transcript, detect_injection, sanitize_output

app = FastAPI(
    title="AI Meeting Summarization API",
    description="FastAPI backend demonstrating prompt injection vulnerability and mitigation.",
    version="1.0.0",
)


class TranscriptRequest(BaseModel):
    transcript: str


class SummaryResponse(BaseModel):
    summary: str
    mode: str
    injection_detected: bool
    matched_patterns: list[str] = []
    warning: str | None = None


def call_llm(system_prompt: str, user_content: str) -> str:
    """Single LLM call point — swapping providers (e.g. to Anthropic Claude,
    as specified in the original project brief) means changing only this
    function. Uses Groq here since that's the key available for testing.

    If no API key is configured, falls back to a clearly-labeled stub
    response rather than failing outright — this lets the security layer
    (validation, injection detection, sanitization) be demonstrated
    end-to-end without a live key. The stub is NOT a real summary; it is
    labeled as such in its own output.
    """
    if not GROQ_API_KEY:
        return (
            "**[DEMO STUB — no GROQ_API_KEY configured, this is not a real LLM summary]**\n\n"
            "## Decisions\n- (would be extracted by the LLM from the transcript)\n\n"
            "## Action Items\n- (would be extracted by the LLM from the transcript)\n\n"
            "## Participants\n- (would be extracted by the LLM from the transcript)\n\n"
        )

    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


@app.get("/")
def root():
    return {"status": "ok", "message": "AI Meeting Summarization API is running."}


@app.post("/summarize/vulnerable", response_model=SummaryResponse)
def summarize_vulnerable(req: TranscriptRequest):
    """VULNERABLE mode: transcript is concatenated directly into the prompt
    with no isolation. Included only for the security demonstration —
    NOT how this should be deployed in production.
    """
    validation = validate_transcript(req.transcript)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    injection = detect_injection(req.transcript)

    prompt = VULNERABLE_PROMPT_TEMPLATE.format(
        system_prompt=VULNERABLE_SYSTEM_PROMPT,
        transcript=req.transcript,
    )

    try:
        raw_summary = call_llm(VULNERABLE_SYSTEM_PROMPT, prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return SummaryResponse(
        summary=sanitize_output(raw_summary),
        mode="vulnerable",
        injection_detected=injection["suspicious"],
        matched_patterns=injection["matched_patterns"],
        warning="Injection pattern detected — vulnerable mode does NOT block execution." if injection["suspicious"] else None,
    )


@app.post("/summarize/secure", response_model=SummaryResponse)
def summarize_secure(req: TranscriptRequest):
    """SECURE mode: validated input, isolated prompt (transcript is clearly
    delimited as data), explicit anti-injection system instructions, and
    sanitized output.
    """
    validation = validate_transcript(req.transcript)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    injection = detect_injection(req.transcript)

    prompt = SECURE_PROMPT_TEMPLATE.format(
        system_prompt=SECURE_SYSTEM_PROMPT,
        transcript=req.transcript,
    )

    try:
        raw_summary = call_llm(SECURE_SYSTEM_PROMPT, prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return SummaryResponse(
        summary=sanitize_output(raw_summary),
        mode="secure",
        injection_detected=injection["suspicious"],
        matched_patterns=injection["matched_patterns"],
        warning="Injection pattern detected in input, but prompt isolation prevented execution." if injection["suspicious"] else None,
    )
