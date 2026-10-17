from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from tts_service.app import app, normalize_text, require_auth, split_sentences


class FakeTokenizer:
    def get_vocab(self) -> dict[str, int]:
        return {"crop": 0, "doctor": 1, " ": 2, ".": 3, "!": 4, "a": 5, "b": 6, "c": 7, "d": 8, "o": 9, "r": 10, "p": 11, "t": 12}


def test_normalize_text_strips_noise() -> None:
    text = "**Hello** https://example.com 😊 Crop Doctor!"
    cleaned = normalize_text(text, FakeTokenizer())
    assert "https" not in cleaned
    assert "**" not in cleaned
    assert "😊" not in cleaned
    assert cleaned == cleaned.lower()


def test_split_sentences_limits_chunk_size() -> None:
    parts = split_sentences("One. Two sentences here. A much longer sentence that should still be split sensibly.", max_length=20)
    assert parts
    assert all(len(part) <= 20 for part in parts)


def test_require_auth_enforces_token(monkeypatch) -> None:
    monkeypatch.setenv("TTS_SERVICE_TOKEN", "secret")
    with pytest.raises(HTTPException):
        require_auth("Bearer wrong")
    require_auth("Bearer secret")
    monkeypatch.delenv("TTS_SERVICE_TOKEN", raising=False)
    require_auth(None)


async def _fake_audio(text: str, language: str) -> bytes:
    return b"ID3test-mp3"


def test_endpoint_allows_open_access_when_token_unset(monkeypatch) -> None:
    monkeypatch.delenv("TTS_SERVICE_TOKEN", raising=False)
    monkeypatch.setattr("tts_service.app.synthesize_audio_bytes", _fake_audio)
    client = TestClient(app)
    response = client.post("/synthesize", json={"text": "Hello", "language": "en"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content.startswith(b"ID3")


def test_endpoint_requires_token_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("TTS_SERVICE_TOKEN", "secret")
    monkeypatch.setattr("tts_service.app.synthesize_audio_bytes", _fake_audio)
    client = TestClient(app)
    assert client.post("/synthesize", json={"text": "Hello", "language": "en"}).status_code == 401
    response = client.post(
        "/synthesize",
        json={"text": "Hello", "language": "en"},
        headers={"Authorization": "Bearer secret"},
    )
    assert response.status_code == 200


def test_input_validation_and_alias_normalization(monkeypatch) -> None:
    monkeypatch.delenv("TTS_SERVICE_TOKEN", raising=False)

    async def fake_synth(text: str, language: str) -> bytes:
        assert language == "lug"
        return b"ID3fake"

    monkeypatch.setattr("tts_service.app.synthesize_audio_bytes", fake_synth)
    client = TestClient(app)
    assert client.post("/", json={"language": "lug"}).status_code == 422
    response = client.post("/", json={"text": "Hello", "language": "lg"})
    assert response.status_code == 200
    assert response.content.startswith(b"ID3")