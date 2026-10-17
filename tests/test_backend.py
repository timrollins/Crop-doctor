import base64
import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
import httpx
from PIL import Image
import pytest

from backend.config import Settings
from backend.diagnosis import parse_identification
from backend.knowledge import KnowledgeBase
from backend.llm_client import LLMClient, LLMRateLimited
from backend.main import create_app


def settings(tmp_path: Path) -> Settings:
    return Settings(
        llm_api_key="",
        llm_model="gemma-test",
        knowledge_dir=str(Path("knowledge")),
        audio_dir=str(tmp_path),
    )


def test_knowledge_loads_and_validates_ids(tmp_path: Path) -> None:
    directory = tmp_path / "knowledge"
    directory.mkdir()
    (directory / "UPPER.JSON").write_text(
        '[{"id":"maize_test","crop":"maize","problem":"test"}]', encoding="utf-8"
    )
    (directory / "bad.json").write_text("{", encoding="utf-8")
    knowledge = KnowledgeBase(directory)
    assert knowledge.get("maize_test")
    assert knowledge.get("with_under_score") is None
    assert knowledge.get("../x") is None


def test_parser_accepts_fenced_and_extra_text() -> None:
    class Knowledge:
        def get(self, value: str) -> dict | None:
            return {} if value == "banana_bxw" else None

    result = parse_identification(
        'Here is the result: ```json {"crop":"banana","problem_id":"banana_bxw","confidence":"high","reason":"wilt"} ```',
        Knowledge(),
    )
    assert result["problem_id"] == "banana_bxw"
    assert result["confidence"] == "high"
    assert parse_identification("garbage", Knowledge())["confidence"] == "low"


def test_image_diagnosis_with_fake_llm(monkeypatch, tmp_path: Path) -> None:
    import backend.main as main

    class FakeLLM:
        def __init__(self, *args: object) -> None:
            pass

        async def answer(self, prompt: str, **kwargs: object) -> str:
            if "Identify" in prompt:
                return '{"crop":"banana","problem_id":"banana_bxw","confidence":"high","reason":"wilt"}'
            return "Report the suspected problem to an agricultural officer. Remove infected plants safely."

    monkeypatch.setattr(main, "LLMClient", FakeLLM)
    image = Image.new("RGB", (1200, 900), "green")
    image_path = tmp_path / "leaf.jpg"
    image.save(image_path)
    encoded = base64.b64encode(image_path.read_bytes()).decode()
    client = TestClient(create_app(settings(tmp_path)))
    response = client.post("/api/diagnose", json={"image_base64": encoded, "language": "lg"})
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "lug"
    assert data["problem_id"] == "banana_bxw"
    assert data["problem"]["id"] == "banana_bxw"


def test_status_and_speak_compatibility(monkeypatch, tmp_path: Path) -> None:
    import backend.main as main

    async def fake_synthesize(text: str, api_url: str, api_key: str, output_dir: str, language: str = "en") -> Path:
        path = Path(output_dir) / "answer.wav"
        path.write_bytes(b"RIFF")
        return path

    monkeypatch.setattr(main, "synthesize", fake_synthesize)
    client = TestClient(create_app(settings(tmp_path)))
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/status").json()["knowledge_entries"] >= 10
    assert client.post("/api/speak", json={"text": "Hello", "language": "en"}).status_code == 200
    assert client.get("/api/speak?text=Hello&language=en").status_code == 200


def test_llm_retries_rate_limit(monkeypatch) -> None:
    responses = iter([
        httpx.Response(429, request=httpx.Request("POST", "https://example.test")),
        httpx.Response(200, json={"ok": True}, request=httpx.Request("POST", "https://example.test")),
    ])

    def handler(request: httpx.Request) -> httpx.Response:
        return next(responses)

    async def no_sleep(delay: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    client = LLMClient("", "key", "gemma-test")

    async def run() -> httpx.Response:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            return await client._request(http_client, "https://example.test")

    assert asyncio.run(run()).status_code == 200


def test_llm_persistent_rate_limit(monkeypatch) -> None:
    request = httpx.Request("POST", "https://example.test")
    transport = httpx.MockTransport(lambda _: httpx.Response(429, request=request))
    async def no_sleep(delay: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    client = LLMClient("", "key", "gemma-test")

    async def run() -> None:
        async with httpx.AsyncClient(transport=transport) as http_client:
            await client._request(http_client, "https://example.test")

    with pytest.raises(LLMRateLimited):
        asyncio.run(run())
