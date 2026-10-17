"""Hosted or experimental Gemma speech-to-text adapters."""

from pathlib import Path
from typing import Any

import base64
import httpx


async def transcribe(
    audio: bytes,
    filename: str,
    api_url: str,
    api_key: str,
    *,
    provider: str = "generic",
    mime_type: str = "audio/webm",
    model: str = "gemma-3-27b-it",
    language: str = "en",
) -> str:
    if provider == "gemma":
        if not api_key:
            raise RuntimeError("Gemma STT is not configured")
        url = f"{(api_url or 'https://generativelanguage.googleapis.com/v1beta').rstrip('/')}/models/{model}:generateContent"
        payload: dict[str, Any] = {"contents": [{"role": "user", "parts": [
            {"text": f"Transcribe this audio exactly as spoken in {language}. Return only the transcript."},
            {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(audio).decode("ascii")}},
        ]}]}
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                response = await client.post(url, headers={"x-goog-api-key": api_key}, json=payload)
                response.raise_for_status()
            except (httpx.HTTPError, KeyError, IndexError) as exc:
                raise RuntimeError("This Gemma model did not accept audio") from exc
        try:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("This Gemma model did not accept audio") from exc
    if not api_url:
        raise RuntimeError("STT_API_URL is not configured")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    files = {"file": (Path(filename).name, audio, mime_type)}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(api_url, files=files, headers=headers)
        response.raise_for_status()
    text = response.json().get("text")
    if not isinstance(text, str):
        raise RuntimeError("STT provider returned no transcript")
    return text
