"""Provider-agnostic HTTP client for an OpenAI-compatible chat endpoint."""

import httpx


class LLMClient:
    def __init__(self, api_url: str, api_key: str, model: str) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.model = model

    async def answer(self, prompt: str) -> str:
        if not self.api_url:
            return (
                "LLM is not configured. Please describe the crop, visible symptoms, "
                "and when the symptoms started so a local agronomist can help."
            )
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
