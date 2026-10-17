"""
backend/tts.py: text + language -> WAV file, returns the URL path.

Usage from FastAPI (Person A):
    from tts import synthesize
    audio_url = synthesize(answer_text, "lug")   # -> "/audio/<hash>.wav"

Requires FastAPI to serve AUDIO_DIR at /audio:
    app.mount("/audio", StaticFiles(directory="audio"), name="audio")
"""
import hashlib
import subprocess
from pathlib import Path
import uuid
import httpx


async def synthesize(
    text: str, api_url: str, api_key: str, output_dir: str, language: str = "en"
) -> Path:
    if not api_url:
        raise RuntimeError("TTS_API_URL is not configured")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            api_url, json={"text": text, "language": language}, headers=headers
        )
        response.raise_for_status()
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f"{uuid.uuid4().hex}.mp3"
    path.write_bytes(response.content)
    return path
