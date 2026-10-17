"""FastAPI application and API routes."""

import base64
import hashlib
import logging
from pathlib import Path
import mimetypes
import time
from typing import Annotated, Any

import httpx
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from .config import Settings, get_settings
from .diagnosis import deterministic_advice, parse_identification
from .images import prepare_image
from .knowledge import KnowledgeBase
from .llm_client import LLMClient, LLMError, LLMRateLimited
from .prompts import advice_prompt, identification_prompt
from .stt import transcribe
from .tts import synthesize

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = {"en": "English", "lug": "Luganda", "sw": "Swahili"}
LANGUAGE_ALIASES = {"lg": "lug", "swa": "sw", "kiswahili": "sw"}


def normalize_language(value: str) -> str:
    language = value.strip().lower()
    language = LANGUAGE_ALIASES.get(language, language)
    if language not in LANGUAGES:
        raise ValueError("language must be en, lug, or sw")
    return language


class DiagnosisRequest(BaseModel):
    question: str = Field(default="", max_length=5000)
    language: str = Field(default="en", max_length=20)
    problem_id: str | None = None
    image_base64: str | None = None
    image_mime_type: str = "image/jpeg"

    @model_validator(mode="after")
    def requires_input(self) -> "DiagnosisRequest":
        if not self.question.strip() and not self.image_base64 and not self.problem_id:
            raise ValueError("provide a question, image, or problem_id")
        return self


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    language: str = Field(default="en", max_length=20)
    problem_id: str | None = None


class DiagnosisResponse(BaseModel):
    answer: str
    advice_text: str
    problem: dict[str, Any] | None = None
    problem_id: str | None = None
    problem_name: str | None = None
    crop: str | None = None
    confidence: str | None = None
    language: str = "en"
    needs_clearer_photo: bool = False
    degraded: bool = False


def _error(exc: Exception) -> HTTPException:
    if isinstance(exc, LLMRateLimited):
        return HTTPException(status_code=429, detail="The advisor is busy, please try again in a minute")
    return HTTPException(status_code=502, detail="The advisor could not answer right now")


def create_app(settings: Settings | None = None) -> FastAPI:
    current = settings or get_settings()
    current.validate()
    knowledge = KnowledgeBase(ROOT / current.knowledge_dir)
    llm = LLMClient(
        current.llm_api_url, current.llm_api_key, current.llm_model, current.llm_provider,
        current.llm_fallback_url, current.llm_fallback_key, current.llm_fallback_model,
    )
    cache: dict[str, tuple[float, DiagnosisResponse]] = {}
    app = FastAPI(title="Crop Doctor", version="1.0.0")
    app.add_middleware(
        CORSMiddleware, allow_origins=current.allowed_origins,
        allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/status")
    async def status() -> dict[str, Any]:
        return {
            "llm_configured": bool(current.llm_api_key),
            "model": current.llm_model,
            "fallback_configured": bool(current.llm_fallback_key),
            "stt_provider": current.stt_provider,
            "stt_configured": bool(current.stt_api_key or current.stt_api_url),
            "tts_configured": bool(current.tts_api_key or current.tts_api_url),
            "knowledge_entries": len(knowledge.list()),
            "cache_seconds": current.response_cache_seconds,
        }

    @app.get("/api/knowledge")
    async def list_knowledge() -> list[dict[str, Any]]:
        return knowledge.list()

    @app.post("/api/diagnose", response_model=DiagnosisResponse)
    async def diagnose(request: DiagnosisRequest) -> DiagnosisResponse:
        try:
            language = normalize_language(request.language)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        image_bytes: bytes | None = None
        image_mime_type = request.image_mime_type
        if request.image_base64:
            try:
                raw = base64.b64decode(request.image_base64, validate=True)
                image_bytes, image_mime_type = prepare_image(
                    raw, current.max_image_side, current.max_upload_mb
                )
            except (ValueError, base64.binascii.Error) as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
        cache_key = hashlib.sha256(
            (image_bytes or b"") + request.question.encode() + language.encode()
            + (request.problem_id or "").encode()
        ).hexdigest()
        cached = cache.get(cache_key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        entry = knowledge.get(request.problem_id)
        confidence = "high" if entry else "low"
        crop = str(entry.get("crop")) if entry else None
        detected_id = request.problem_id
        if not entry:
            started = time.monotonic()
            try:
                identified = parse_identification(
                    await llm.answer(
                        identification_prompt(request.question, knowledge.catalog()),
                        image_bytes=image_bytes, image_mime_type=image_mime_type,
                    ),
                    knowledge,
                )
            except LLMError as exc:
                raise _error(exc) from exc
            logger.info("identify completed in %.3fs language=%s", time.monotonic() - started, language)
            detected_id = identified["problem_id"]
            confidence = identified["confidence"]
            entry = knowledge.get(detected_id)
            crop = identified["crop"] if identified["crop"] != "unknown" else (str(entry.get("crop")) if entry else None)
        needs_clearer = detected_id == "unknown" or confidence == "low"
        started = time.monotonic()
        degraded = False
        try:
            advice = await llm.answer(
                advice_prompt(request.question, entry, LANGUAGES[language], confidence),
                image_bytes=image_bytes, image_mime_type=image_mime_type,
            )
        except LLMError:
            advice = deterministic_advice(entry)
            degraded = True
        logger.info("advise completed in %.3fs language=%s", time.monotonic() - started, language)
        result = DiagnosisResponse(
            answer=advice, advice_text=advice, problem=entry, problem_id=detected_id,
            problem_name=str(entry.get("problem")) if entry else None, crop=crop,
            confidence=confidence, language=language, needs_clearer_photo=needs_clearer,
            degraded=degraded,
        )
        if current.response_cache_seconds > 0:
            if len(cache) >= 100:
                cache.pop(next(iter(cache)))
            cache[cache_key] = (time.monotonic() + current.response_cache_seconds, result)
        return result

    @app.post("/api/ask", response_model=DiagnosisResponse)
    async def ask(request: AskRequest) -> DiagnosisResponse:
        try:
            language = normalize_language(request.language)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        entries = []
        if request.problem_id and knowledge.get(request.problem_id):
            entries.append(knowledge.get(request.problem_id))
        question_lower = request.question.lower()
        for candidate in knowledge.list():
            if candidate in entries:
                continue
            if len(entries) >= 3:
                break
            if str(candidate.get("crop", "")).lower() in question_lower or str(candidate.get("problem", "")).lower() in question_lower:
                entries.append(candidate)
        context = entries[0] if len(entries) == 1 else {"related_entries": entries}
        try:
            advice = await llm.answer(advice_prompt(request.question, context, LANGUAGES[language], "medium"))
        except LLMError as exc:
            raise _error(exc) from exc
        entry = entries[0] if entries else None
        return DiagnosisResponse(
            answer=advice, advice_text=advice, problem=entry, problem_id=request.problem_id,
            language=language,
        )

    @app.post("/api/transcribe")
    async def transcribe_audio(
        file: Annotated[UploadFile, File()],
        language: Annotated[str, Query()] = "en",
    ) -> dict[str, str]:
        try:
            normalized = normalize_language(language)
            audio = await file.read()
            if len(audio) > current.max_upload_mb * 1024 * 1024:
                raise ValueError("Audio is too large, please record a shorter question")
            started = time.monotonic()
            text = await transcribe(
                audio, file.filename or "audio.webm", current.stt_api_url, current.stt_api_key,
                provider=current.stt_provider, mime_type=file.content_type or "audio/webm",
                model=current.llm_model, language=normalized,
            )
            logger.info("stt completed in %.3fs language=%s", time.monotonic() - started, normalized)
            return {"text": text}
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except (RuntimeError, httpx.HTTPError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    async def speak_impl(text: str, language: str) -> FileResponse:
        try:
            normalized = normalize_language(language)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        started = time.monotonic()
        try:
            path = await synthesize(text, current.tts_api_url, current.tts_api_key, current.audio_dir, normalized)
        except (RuntimeError, httpx.HTTPError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        logger.info("tts completed in %.3fs language=%s", time.monotonic() - started, normalized)
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return FileResponse(path, media_type=media_type, filename=path.name)

    @app.post("/api/speak")
    async def speak_post(payload: dict[str, str]) -> FileResponse:
        text = payload.get("text", "")
        if not 1 <= len(text) <= 5000:
            raise HTTPException(status_code=422, detail="text must contain 1 to 5000 characters")
        return await speak_impl(text, payload.get("language", "en"))

    @app.get("/api/speak")
    async def speak_get(
        text: Annotated[str, Query(min_length=1, max_length=5000)],
        language: Annotated[str, Query()] = "en",
    ) -> FileResponse:
        return await speak_impl(text, language)

    frontend = ROOT / "frontend"
    if frontend.is_dir():
        app.mount("/static", StaticFiles(directory=frontend), name="static")

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(frontend / "index.html")

    return app


app = create_app()
