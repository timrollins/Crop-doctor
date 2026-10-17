# Crop Doctor

Crop Doctor is an API-only, HTTPS-ready crop advisor for Ugandan smallholder
farmers. The backend uses **Gemma through Google AI Studio by default** and can
fall back to an OpenRouter-compatible endpoint. It accepts symptom questions
and optional leaf photos, then returns cautious, practical advice grounded in
the local JSON knowledge base.

## Current Person A deliverables

- FastAPI app with `/api/health`, `/api/diagnose`, `/api/ask`, `/api/transcribe`,
  and `/api/speak`.
- Provider-neutral `backend/llm_client.py` with native Google AI Studio
  `generateContent` requests, image input, and optional OpenRouter fallback.
- Prompt construction that limits advice to low-risk steps and asks for local
  extension help when uncertain.
- JSON knowledge lookup by problem ID.
- Environment-based configuration; no API key belongs in the repository.
- Render/Railway-compatible `Procfile`.

## What remains for Person B

1. Expand [`knowledge/`](knowledge) to 8–10 reviewed entries with local
   extension-worker guidance. Do not add pesticide dosages without a trusted
   source.
2. Add a short demo flow and screenshots/video to the README, then test the
   deployed URL from a real phone.

The browser app supports camera photo capture, microphone transcription,
English/Kiswahili/Luganda follow-up questions, and automatic audio playback
with replay for both diagnosis and follow-up answers.

## Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload
```

Set `LLM_API_KEY` to a Google AI Studio key. The default model is
`gemma-3-27b-it`; set `LLM_MODEL` to another model only after verifying that
the account/API supports it. `LLM_API_URL` may be left empty for Google AI
Studio. Optional `LLM_FALLBACK_KEY` enables the OpenRouter fallback shown in
`.env.example`.

Open <http://localhost:8000>. Without an LLM key the app still starts and
returns a safe configuration message, which keeps frontend development
possible without credentials.

## Deploy

Use the included [`Procfile`](Procfile) on Render or Railway. Configure the
same environment variables in the hosting dashboard, connect deployment to
`main`, and verify `/api/health` before testing camera and microphone access.
The browser must use the host's public HTTPS URL for camera/microphone APIs.

## Test

```bash
pytest
```

See [`CONTRACT.md`](CONTRACT.md) for request and response shapes.
