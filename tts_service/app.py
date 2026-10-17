from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
import subprocess
import wave
from array import array
from collections import OrderedDict
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "en": "facebook/mms-tts-eng",
    "lug": "facebook/mms-tts-lug",
    "sw": "facebook/mms-tts-swh",
}

MAX_INPUT_LENGTH = 1500
MAX_SENTENCE_LENGTH = 200
MAX_CACHE_ITEMS = 100
SILENCE_SECONDS = 0.15

URL_RE = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[(.*?)\]\((.*?)\)")
CODE_BLOCK_RE = re.compile(r"```.*?```", flags=re.DOTALL)
INLINE_CODE_RE = re.compile(r"`([^`]*)`")
EMOJI_RE = re.compile(r"[\U00010000-\U0010ffff]")
WHITESPACE_RE = re.compile(r"\s+")
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class ModelBundle:
    tokenizer: Any
    model: Any
    sample_rate: int


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_INPUT_LENGTH)
    language: str = Field(default="en")


_MODEL_BUNDLES: dict[str, ModelBundle] = {}
_AUDIO_CACHE: OrderedDict[str, bytes] = OrderedDict()


def normalize_language(language: str) -> str:
    value = (language or "en").strip().lower()
    if value == "lg":
        value = "lug"
    if value not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=422, detail="Unsupported language.")
    return value


def strip_markdown(text: str) -> str:
    cleaned = CODE_BLOCK_RE.sub(" ", text)
    cleaned = INLINE_CODE_RE.sub(r"\1", cleaned)
    cleaned = MARKDOWN_LINK_RE.sub(r"\1", cleaned)
    cleaned = re.sub(r"[*_~>#]", " ", cleaned)
    return cleaned


def filter_to_tokenizer_vocab(text: str, tokenizer: Any | None) -> str:
    if tokenizer is None or not hasattr(tokenizer, "get_vocab"):
        return text

    try:
        vocab = tokenizer.get_vocab()
    except Exception:
        return text

    if not isinstance(vocab, dict) or not vocab:
        return text

    allowed_characters = set()
    for token in vocab.keys():
        allowed_characters.update(token)

    return "".join(character if character in allowed_characters or character.isspace() else " " for character in text)


def normalize_text(text: str, tokenizer: Any | None = None) -> str:
    cleaned = text.strip().lower()
    cleaned = URL_RE.sub(" ", cleaned)
    cleaned = strip_markdown(cleaned)
    cleaned = EMOJI_RE.sub(" ", cleaned)
    cleaned = filter_to_tokenizer_vocab(cleaned, tokenizer)
    cleaned = WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned[:MAX_INPUT_LENGTH]


def split_sentences(text: str, max_length: int = MAX_SENTENCE_LENGTH) -> list[str]:
    compact = WHITESPACE_RE.sub(" ", text).strip()
    if not compact:
        return []

    raw_parts = [part.strip() for part in SENTENCE_BOUNDARY_RE.split(compact) if part.strip()]
    if not raw_parts:
        raw_parts = [compact]

    chunks: list[str] = []
    current = ""

    def flush_current() -> None:
        nonlocal current
        if current:
            chunks.append(current)
            current = ""

    for part in raw_parts:
        if len(part) <= max_length:
            candidate = f"{current} {part}".strip()
            if candidate and len(candidate) <= max_length:
                current = candidate
                continue
            flush_current()
            current = part
            continue

        flush_current()
        words = part.split()
        buffer = ""
        for word in words:
            candidate = f"{buffer} {word}".strip()
            if candidate and len(candidate) <= max_length:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                buffer = word
        if buffer:
            chunks.append(buffer)

    flush_current()
    return chunks


def _cache_key(language: str, normalized_text: str) -> str:
    digest = hashlib.sha256(f"{language}:{normalized_text}".encode("utf-8")).hexdigest()
    return digest


def _cache_get(cache_key: str) -> bytes | None:
    value = _AUDIO_CACHE.get(cache_key)
    if value is not None:
        _AUDIO_CACHE.move_to_end(cache_key)
    return value


def _cache_put(cache_key: str, audio_bytes: bytes) -> None:
    _AUDIO_CACHE[cache_key] = audio_bytes
    _AUDIO_CACHE.move_to_end(cache_key)
    while len(_AUDIO_CACHE) > MAX_CACHE_ITEMS:
        _AUDIO_CACHE.popitem(last=False)


def _load_bundle(language: str) -> ModelBundle:
    cached = _MODEL_BUNDLES.get(language)
    if cached is not None:
        return cached

    model_id = SUPPORTED_LANGUAGES[language]

    try:
        from transformers import AutoTokenizer, VitsModel
    except Exception as exc:  # pragma: no cover - dependency issue is deployment-specific
        raise RuntimeError("transformers is required for TTS synthesis") from exc

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = VitsModel.from_pretrained(model_id)
    model.to("cpu")
    model.eval()
    sample_rate = int(getattr(model.config, "sampling_rate", 24000))
    bundle = ModelBundle(tokenizer=tokenizer, model=model, sample_rate=sample_rate)
    _MODEL_BUNDLES[language] = bundle
    return bundle


def _waveform_to_samples(waveform: Any) -> list[float]:
    if hasattr(waveform, "detach"):
        waveform = waveform.detach().cpu().flatten().tolist()
    elif isinstance(waveform, tuple):
        waveform = list(waveform)
    elif hasattr(waveform, "tolist"):
        waveform = waveform.tolist()

    if waveform and isinstance(waveform[0], list):
        waveform = [sample for row in waveform for sample in row]

    return [max(-1.0, min(1.0, float(sample))) for sample in waveform]


def _render_waveform(bundle: ModelBundle, text: str) -> bytes:
    chunks = split_sentences(text)
    if not chunks:
        raise HTTPException(status_code=422, detail="Text is empty after cleaning.")

    samples = array("h")
    pause_samples = max(1, int(bundle.sample_rate * SILENCE_SECONDS))

    try:
        import torch
    except Exception as exc:  # pragma: no cover - dependency issue is deployment-specific
        raise RuntimeError("torch is required for TTS synthesis") from exc

    for index, chunk in enumerate(chunks):
        inputs = bundle.tokenizer(chunk, return_tensors="pt")
        with torch.no_grad():
            output = bundle.model(**inputs)
        waveform = getattr(output, "waveform", output)
        for sample in _waveform_to_samples(waveform):
            samples.append(int(sample * 32767))
        if index < len(chunks) - 1:
            samples.extend([0] * pause_samples)

    wav_buffer = BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(bundle.sample_rate)
        wav_file.writeframes(samples.tobytes())

    return wav_buffer.getvalue()


def _encode_mp3(wav_bytes: bytes) -> bytes:
    process = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "wav", "-i", "pipe:0", "-f", "mp3", "pipe:1"],
        input=wav_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    if process.returncode != 0:
        raise RuntimeError(process.stderr.decode("utf-8", errors="ignore") or "ffmpeg failed to encode MP3")

    mp3_bytes = process.stdout
    if not (mp3_bytes.startswith(b"ID3") or mp3_bytes.startswith(b"\xff\xfb") or mp3_bytes.startswith(b"\xff\xf3") or mp3_bytes.startswith(b"\xff\xfa")):
        raise RuntimeError("Encoded audio is not valid MP3")
    return mp3_bytes


async def synthesize_audio_bytes(text: str, language: str) -> bytes:
    normalized_language = normalize_language(language)
    bundle = _load_bundle(normalized_language)
    normalized_text = normalize_text(text, bundle.tokenizer)
    if not normalized_text:
        raise HTTPException(status_code=422, detail="Text is empty after cleaning.")

    cache_key = _cache_key(normalized_language, normalized_text)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    wav_bytes = await asyncio.to_thread(_render_waveform, bundle, normalized_text)
    mp3_bytes = await asyncio.to_thread(_encode_mp3, wav_bytes)
    _cache_put(cache_key, mp3_bytes)
    return mp3_bytes


def require_auth(authorization: str | None) -> None:
    expected_token = os.getenv("TTS_SERVICE_TOKEN", "").strip()
    if not expected_token:
        return
    if authorization != f"Bearer {expected_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


async def warmup_models() -> None:
    phrase = "Crop Doctor warm up."
    for language_code in SUPPORTED_LANGUAGES:
        try:
            await synthesize_audio_bytes(phrase, language_code)
        except Exception as exc:  # pragma: no cover - deployment-specific logging
            logger.info("TTS warm-up skipped for %s: %s", language_code, exc)


def create_app() -> FastAPI:
    app = FastAPI(title="Crop Doctor TTS", version="1.0.0")

    @app.on_event("startup")
    async def _startup() -> None:
      asyncio.create_task(warmup_models())

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    async def synthesize_endpoint(payload: SpeechRequest, authorization: str | None = Header(default=None)) -> Response:
        require_auth(authorization)
        language = normalize_language(payload.language)
        audio_bytes = await synthesize_audio_bytes(payload.text, language)
        return Response(content=audio_bytes, media_type="audio/mpeg")

    app.post("/synthesize")(synthesize_endpoint)
    app.post("/")(synthesize_endpoint)
    return app


app = create_app()
