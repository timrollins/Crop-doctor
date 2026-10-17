"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_api_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "gemma-3-27b-it"
    llm_provider: str = "google"
    llm_fallback_url: str = ""
    llm_fallback_key: str = ""
    llm_fallback_model: str = ""
    stt_provider: str = "generic"
    stt_api_url: str = ""
    stt_api_key: str = ""
    tts_api_url: str = ""
    tts_api_key: str = ""
    knowledge_dir: str = "knowledge"
    audio_dir: str = "backend/audio_out"
    cors_origins: str = "*"
    response_cache_seconds: int = 0
    max_image_side: int = 768
    max_upload_mb: int = 10

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_api_url=os.getenv("LLM_API_URL", ""),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", "gemma-3-27b-it"),
            llm_provider=os.getenv("LLM_PROVIDER", "google"),
            llm_fallback_url=os.getenv("LLM_FALLBACK_URL", ""),
            llm_fallback_key=os.getenv("LLM_FALLBACK_KEY", ""),
            llm_fallback_model=os.getenv("LLM_FALLBACK_MODEL", ""),
            stt_provider=os.getenv("STT_PROVIDER", "generic"),
            stt_api_url=os.getenv("STT_API_URL", ""),
            stt_api_key=os.getenv("STT_API_KEY", ""),
            tts_api_url=os.getenv("TTS_API_URL", ""),
            tts_api_key=os.getenv("TTS_API_KEY", ""),
            knowledge_dir=os.getenv("KNOWLEDGE_DIR", "knowledge"),
            audio_dir=os.getenv("AUDIO_DIR", "backend/audio_out"),
            cors_origins=os.getenv("CORS_ORIGINS", "*"),
            response_cache_seconds=int(os.getenv("RESPONSE_CACHE_SECONDS", "0")),
            max_image_side=int(os.getenv("MAX_IMAGE_SIDE", "768")),
            max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "10")),
        )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate(self) -> None:
        models = [self.llm_model]
        if self.llm_fallback_model:
            models.append(self.llm_fallback_model)
        if any("gemma" not in model.lower() for model in models):
            raise ValueError("Only Gemma models are allowed; check LLM_MODEL and LLM_FALLBACK_MODEL")
        if self.stt_provider not in {"generic", "gemma"}:
            raise ValueError("STT_PROVIDER must be 'generic' or 'gemma'")


@lru_cache
def get_settings() -> Settings:
    settings = Settings.from_env()
    settings.validate()
    return settings
