"""Run one diagnosis through the configured local backend."""

import argparse
import asyncio
import base64
import json
from pathlib import Path

from backend.config import get_settings
from backend.main import DiagnosisRequest, create_app


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", type=Path)
    parser.add_argument("--language", default="en")
    parser.add_argument("--question", default="")
    args = parser.parse_args()
    settings = get_settings()
    if not settings.llm_api_key and not settings.llm_fallback_key:
        print("No LLM key is configured. Add LLM_API_KEY to .env before trying a live diagnosis.")
        return
    # Constructing the request exercises validation; the HTTP route remains the source of truth.
    request = DiagnosisRequest(
        image_base64=base64.b64encode(args.image_path.read_bytes()).decode(),
        image_mime_type="image/jpeg",
        language=args.language,
        question=args.question,
    )
    app = create_app(settings)
    for route in app.routes:
        if getattr(route, "path", None) == "/api/diagnose":
            response = await route.endpoint(request)
            print(json.dumps(response.model_dump(), indent=2))
            return


if __name__ == "__main__":
    asyncio.run(main())
