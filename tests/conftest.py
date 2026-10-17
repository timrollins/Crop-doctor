"""Offline test configuration."""

import os

os.environ["PYTHON_DOTENV_DISABLED"] = "1"

for _name in (
    "LLM_API_URL", "LLM_API_KEY", "LLM_FALLBACK_URL",
    "LLM_FALLBACK_KEY", "STT_API_URL", "STT_API_KEY",
    "TTS_API_URL", "TTS_API_KEY",
):
    os.environ[_name] = ""
os.environ["LLM_MODEL"] = "gemma-3-27b-it"
os.environ["LLM_FALLBACK_MODEL"] = ""
