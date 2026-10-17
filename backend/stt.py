"""Hosted speech-to-text adapter."""

from pathlib import Path
import httpx


async def transcribe(audio: bytes, filename: str, api_url: str, api_key: str) -> str:
    if not api_url:
        raise RuntimeError("STT_API_URL is not configured")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    files = {"file": (Path(filename).name, audio, "audio/webm")}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(api_url, files=files, headers=headers)
        response.raise_for_status()
    data = response.json()
    text = data.get("text")
    if not isinstance(text, str):
        raise RuntimeError("STT provider returned no transcript")
    return text
