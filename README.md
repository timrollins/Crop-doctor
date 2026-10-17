# Crop Doctor

Crop Doctor is a small FastAPI application that helps farmers turn crop
symptoms into cautious, practical next steps. It serves a browser frontend and
can connect to hosted LLM, speech-to-text, and text-to-speech providers.

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload
```

Open <http://localhost:8000>. Without `LLM_API_URL`, the diagnosis endpoint
returns a safe configuration message, so the app can be developed without
credentials.

Provider URLs and keys are configured only through environment variables. See
[`.env.example`](.env.example) and [`CONTRACT.md`](CONTRACT.md) for the
available settings and API shapes.

## Test

```bash
pytest
```