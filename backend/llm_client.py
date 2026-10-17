"""Small provider-neutral client for Gemma-compatible APIs."""

import asyncio
import base64
from typing import Any

import httpx


class LLMError(RuntimeError):
    """Base class for provider failures."""


class LLMRateLimited(LLMError):
    """The provider rejected a request because of rate limits."""


class LLMUnavailable(LLMError):
    """The provider was unavailable or returned an invalid response."""


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
        temperature: float = 0.2,
        max_output_tokens: int = 600,
    ) -> str:
        if not self.api_key and not self.fallback_key:
            return "The crop advisor is not configured yet. Please try again later."
        try:
            return await self._answer_with(
                self.api_url,
                self.api_key,
                self.model,
                prompt,
                image_bytes,
                image_mime_type,
                temperature,
                max_output_tokens,
            )
        except (LLMRateLimited, LLMUnavailable):
            if not self.fallback_url or not self.fallback_key:
                raise
            return await self._answer_with(
                self.fallback_url,
                self.fallback_key,
                self.fallback_model or self.model,
                prompt,
                image_bytes,
                image_mime_type,
                temperature,
                max_output_tokens,
            )

    async def _answer_with(
        self,
        api_url: str,
        api_key: str,
        model: str,
        prompt: str,
        image_bytes: bytes | None,
        image_mime_type: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        if self.provider == "google" or api_url.startswith("https://generativelanguage.googleapis.com"):
            return await self._google_answer(
                api_url, api_key, model, prompt, image_bytes, image_mime_type,
                temperature, max_output_tokens,
            )
        return await self._openai_compatible_answer(
            api_url, api_key, model, prompt, image_bytes, image_mime_type,
            temperature, max_output_tokens,
        )

    async def _request(self, client: httpx.AsyncClient, url: str, **kwargs: Any) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = await client.post(url, **kwargs)
                if response.status_code in {429, 500, 502, 503, 504}:
                    if attempt < 2:
                        retry_after = response.headers.get("Retry-After", "")
                        delay = float(retry_after) if retry_after.replace(".", "", 1).isdigit() else attempt + 1
                        await asyncio.sleep(min(delay, 5) if delay <= 5 else attempt + 1)
                        continue
                    if response.status_code == 429:
                        raise LLMRateLimited("LLM provider rate limited the request")
                    raise LLMUnavailable("LLM provider is unavailable")
                response.raise_for_status()
                return response
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(attempt + 1)
                    continue
                raise LLMUnavailable("LLM provider timed out") from exc
            except httpx.HTTPStatusError as exc:
                raise LLMUnavailable("LLM provider rejected the request") from exc
        raise LLMUnavailable("LLM provider request failed") from last_error

    async def _google_answer(
        self,
        api_url: str,
        api_key: str,
        model: str,
        prompt: str,
        image_bytes: bytes | None,
        image_mime_type: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        api_url = api_url or "https://generativelanguage.googleapis.com/v1beta"
        parts: list[dict[str, Any]] = [{"text": prompt}]
        if image_bytes:
            parts.append({"inline_data": {
                "mime_type": image_mime_type,
                "data": base64.b64encode(image_bytes).decode("ascii"),
            }})
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await self._request(
                client,
                f"{api_url.rstrip('/')}/models/{model}:generateContent",
                headers={"x-goog-api-key": api_key},
                json=payload,
            )
        try:
            return self._google_text(response.json())
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMUnavailable("Google AI returned no answer") from exc

    async def _openai_compatible_answer(
        self,
        api_url: str,
        api_key: str,
        model: str,
        prompt: str,
        image_bytes: bytes | None,
        image_mime_type: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image_bytes:
            content.append({"type": "image_url", "image_url": {
                "url": f"data:{image_mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}",
            }})
        async with httpx.AsyncClient(timeout=60) as client:
            response = await self._request(
                client,
                f"{api_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": content}],
                    "max_tokens": max_output_tokens,
                    "temperature": temperature,
                },
            )
        try:
            text = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMUnavailable("LLM provider returned no answer") from exc
        if not isinstance(text, str):
            raise LLMUnavailable("LLM provider returned an invalid answer")
        return text

    @staticmethod
    def _google_text(data: dict[str, Any]) -> str:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(part["text"] for part in parts if isinstance(part.get("text"), str))
        if not text:
            raise ValueError("empty response")
        return text
