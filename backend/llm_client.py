"""Small provider-neutral client for hosted Gemma/Gemini-compatible APIs."""

import base64
from typing import Any

import httpx


class LLMClient:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model: str,
        provider: str = "google",
        fallback_url: str = "",
        fallback_key: str = "",
        fallback_model: str = "",
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.fallback_url = fallback_url.rstrip("/")
        self.fallback_key = fallback_key
        self.fallback_model = fallback_model

    async def answer(
        self,
        prompt: str,
        image_bytes: bytes | None = None,
        image_mime_type: str = "image/jpeg",
    ) -> str:
        if not self.api_key and not self.fallback_key:
            return "The crop advisor is not configured yet. Please try again later."

        try:
            if self.provider == "google":
                return await self._google_answer(prompt, image_bytes, image_mime_type)
            return await self._openai_compatible_answer(
                self.api_url, self.api_key, self.model, prompt, image_bytes, image_mime_type
            )
        except httpx.HTTPError:
            if not self.fallback_url or not self.fallback_key:
                raise
            return await self._openai_compatible_answer(
                self.fallback_url,
                self.fallback_key,
                self.fallback_model or self.model,
                prompt,
                image_bytes,
                image_mime_type,
            )

    async def _google_answer(
        self, prompt: str, image_bytes: bytes | None, image_mime_type: str
    ) -> str:
        if not self.api_url:
            self.api_url = "https://generativelanguage.googleapis.com/v1beta"
        parts: list[dict[str, Any]] = [{"text": prompt}]
        if image_bytes:
            parts.append(
                {
                    "inline_data": {
                        "mime_type": image_mime_type,
                        "data": base64.b64encode(image_bytes).decode("ascii"),
                    }
                }
            )
        url = f"{self.api_url}/models/{self.model}:generateContent"
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json={"contents": [{"role": "user", "parts": parts}]},
            )
            response.raise_for_status()
        data = response.json()
        return self._google_text(data)

    async def _openai_compatible_answer(
        self,
        api_url: str,
        api_key: str,
        model: str,
        prompt: str,
        image_bytes: bytes | None,
        image_mime_type: str,
    ) -> str:
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image_bytes:
            encoded = base64.b64encode(image_bytes).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_mime_type};base64,{encoded}"
                    },
                }
            )
        headers = {"Authorization": f"Bearer {api_key}"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{api_url}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": content}],
                    "max_tokens": 400,
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
        data = response.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("LLM provider returned no answer") from exc
        if not isinstance(text, str):
            raise RuntimeError("LLM provider returned an invalid answer")
        return text

    @staticmethod
    def _google_text(data: dict[str, Any]) -> str:
        try:
            parts = data["candidates"][0]["content"]["parts"]
            text = "".join(part["text"] for part in parts if isinstance(part.get("text"), str))
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Google AI returned no answer") from exc
        if not text:
            raise RuntimeError("Google AI returned an empty answer")
        return text
