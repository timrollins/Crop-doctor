"""Application configuration loaded from environment variables."""

from functools import lru_cache
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    llm_api_url: str = os.getenv("LLM_API_URL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "crop-doctor")
    stt_api_url: str = os.getenv("STT_API_URL", "")
    stt_api_key: str = os.getenv("STT_API_KEY", "")
    tts_api_url: str = os.getenv("TTS_API_URL", "")
    tts_api_key: str = os.getenv("TTS_API_KEY", "")
    knowledge_dir: str = os.getenv("KNOWLEDGE_DIR", "knowledge")
    audio_dir: str = os.getenv("AUDIO_DIR", "backend/audio_out")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
