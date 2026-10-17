"""FastAPI application and API routes."""

from pathlib import Path
from typing import Annotated

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi import Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import base64

from .config import get_settings
from .knowledge import KnowledgeBase
from .llm_client import LLMClient
from .prompts import diagnosis_prompt
from .stt import transcribe
from .tts import synthesize

ROOT = Path(__file__).resolve().parent.parent
settings = get_settings()
knowledge = KnowledgeBase(ROOT / settings.knowledge_dir)
llm = LLMClient(
    settings.llm_api_url,
    settings.llm_api_key,
    settings.llm_model,
    settings.llm_provider,
    settings.llm_fallback_url,
    settings.llm_fallback_key,
    settings.llm_fallback_model,
)

app = FastAPI(title="Crop Doctor", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DiagnosisRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    problem_id: str | None = None
    image_base64: str | None = None
    image_mime_type: str = "image/jpeg"


class DiagnosisResponse(BaseModel):
    answer: str
    problem: dict | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    language: str = Field(default="en", min_length=2, max_length=20)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/knowledge")
async def list_knowledge() -> list[dict]:
    return knowledge.list()


@app.post("/api/diagnose", response_model=DiagnosisResponse)
async def diagnose(request: DiagnosisRequest) -> DiagnosisResponse:
    entry = knowledge.get(request.problem_id) if request.problem_id else None
    image_bytes = None
    if request.image_base64:
        try:
            image_bytes = base64.b64decode(request.image_base64, validate=True)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="image_base64 is invalid") from exc
    try:
        answer = await llm.answer(
            diagnosis_prompt(request.question, entry),
            image_bytes=image_bytes,
            image_mime_type=request.image_mime_type,
        )
    except (KeyError, RuntimeError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=502, detail="LLM provider request failed") from exc
    return DiagnosisResponse(answer=answer, problem=entry)


@app.post("/api/ask", response_model=DiagnosisResponse)
async def ask(request: AskRequest) -> DiagnosisResponse:
    prompt = (
        "Answer this farmer's follow-up question in 3 to 5 short sentences. "
        f"Use clear language and reply in {request.language} if possible. "
        "Do not invent pesticide dosages; recommend a local extension worker when uncertain.\n"
        f"Question: {request.question}"
    )
    try:
        answer = await llm.answer(prompt)
    except (KeyError, RuntimeError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=502, detail="LLM provider request failed") from exc
    return DiagnosisResponse(answer=answer)


@app.post("/api/transcribe")
async def transcribe_audio(file: Annotated[UploadFile, File()]) -> dict[str, str]:
    try:
        text = await transcribe(
            await file.read(), file.filename or "audio.webm",
            settings.stt_api_url, settings.stt_api_key,
        )
    except (RuntimeError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"text": text}


@app.post("/api/speak")
async def speak(text: Annotated[str, Query(min_length=1, max_length=5000)]) -> FileResponse:
    try:
        path = await synthesize(text, settings.tts_api_url, settings.tts_api_key, settings.audio_dir)
    except (RuntimeError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return FileResponse(path, media_type="audio/mpeg", filename=path.name)


frontend = ROOT / "frontend"
if frontend.is_dir():
    app.mount("/static", StaticFiles(directory=frontend), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(frontend / "index.html")
