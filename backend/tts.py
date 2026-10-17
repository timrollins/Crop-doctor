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

import scipy.io.wavfile as wavfile
import torch
from transformers import AutoTokenizer, VitsModel

AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

MMS_MODELS = {"lug": "facebook/mms-tts-lug", "sw": "facebook/mms-tts-swh"}
_loaded = {}  # lang -> (tokenizer, model); loaded once, reused


def _get_mms(lang: str):
    if lang not in _loaded:
        name = MMS_MODELS[lang]
        _loaded[lang] = (AutoTokenizer.from_pretrained(name), VitsModel.from_pretrained(name))
    return _loaded[lang]


def _speak_mms(lang: str, text: str, out: Path) -> None:
    tokenizer, model = _get_mms(lang)
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        wav = model(**inputs).waveform[0].numpy()
    wavfile.write(str(out), model.config.sampling_rate, wav)


def _speak_piper(text: str, out: Path) -> None:
    subprocess.run(
        ["python", "-m", "piper", "-m", "en_US-lessac-medium",
         "--data-dir", "voices", "-f", str(out)],
        input=text.encode(), check=True,
    )


def synthesize(text: str, lang: str) -> str:
    """Return a URL path like /audio/ab12cd.wav. Same text+lang is cached."""
    if lang not in ("en", *MMS_MODELS):
        raise ValueError(f"Unsupported language: {lang}")
    key = hashlib.sha1(f"{lang}:{text}".encode()).hexdigest()[:16]
    out = AUDIO_DIR / f"{key}.wav"
    if not out.exists():
        if lang == "en":
            _speak_piper(text, out)
        else:
            _speak_mms(lang, text, out)
    return f"/audio/{out.name}"


def warm_up() -> None:
    """Call once at server startup so the first request isn't slow."""
    for lang in MMS_MODELS:
        _get_mms(lang)