# Run me first

## What this is

Crop Doctor is a FastAPI web app for identifying crop problems with Gemma and
giving short, knowledge-grounded advice. It can also connect speech-to-text
and text-to-speech services.

## Prerequisites

Use Linux with Python 3.11 or newer and git:

```bash
python3 --version
git --version
```

## One-time setup

```bash
cd ~/"hacking for good"/Crop-doctor
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

Never commit `.env` or share its contents.

## Get the API key and exact model ID

1. Open <https://aistudio.google.com> and sign in.
2. Choose **Get API key**, create or select a project, and copy the key into
   `LLM_API_KEY` in `.env`.
3. In the AI Studio model list, find the exact Gemma 4 model identifier
   available to your account and put it in `LLM_MODEL`.
4. Confirm that the model accepts image input. Also check audio input if you
   plan to test the experimental Gemma STT provider.
5. The model ID must contain `gemma`. Do not use Gemini or another LLM.

## Environment variables

| Name | Required? | Example | Where to get it | Notes |
|---|---|---|---|---|
| `LLM_PROVIDER` | No | `google` | This app | Keep `google` for AI Studio. |
| `LLM_API_URL` | No | empty | AI Studio default | Leave empty for the standard endpoint. |
| `LLM_API_KEY` | For live advice | `your-key` | Google AI Studio | Keep secret. |
| `LLM_MODEL` | For live advice | `gemma-model-id` | AI Studio model list | Exact ID, containing `gemma`. |
| `LLM_FALLBACK_URL` | No | OpenRouter URL | OpenRouter | Optional Gemma-compatible fallback. |
| `LLM_FALLBACK_KEY` | No | `your-key` | OpenRouter | Optional and secret. |
| `LLM_FALLBACK_MODEL` | No | `google/gemma-model-id` | OpenRouter | Must contain `gemma` when set. |
| `STT_PROVIDER` | No | `generic` | This app | `generic` or experimental `gemma`. |
| `STT_API_URL` | For generic STT | `https://...` | Person B/provider | HTTP multipart endpoint. |
| `STT_API_KEY` | Provider-dependent | `your-key` | STT provider | Optional for providers without auth. |
| `TTS_API_URL` | For audio | `https://...` | Person B/provider | TTS endpoint. |
| `TTS_API_KEY` | Provider-dependent | `your-key` | TTS provider | Optional for providers without auth. |
| `KNOWLEDGE_DIR` | No | `knowledge` | This repo | JSON knowledge directory. |
| `AUDIO_DIR` | No | `backend/audio_out` | This repo | Generated audio output. |
| `CORS_ORIGINS` | No | `*` | Deployment config | Comma-separated origins. |
| `RESPONSE_CACHE_SECONDS` | No | `0` | This app | In-memory demo cache TTL. |
| `MAX_IMAGE_SIDE` | No | `768` | This app | Longest resized image side. |
| `MAX_UPLOAD_MB` | No | `10` | This app | Image/audio upload limit. |

## Run locally

```bash
cd ~/"hacking for good"/Crop-doctor
source .venv/bin/activate
uvicorn backend.main:app --reload
```

Open <http://localhost:8000>. In another terminal:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/status
```

The health response must be `{"status":"ok"}`.

## Try the pipeline without the frontend

```bash
source .venv/bin/activate
scripts/try_diagnose.py tests/banana-leaf.webp --language sw
```

For a direct image request, encode an image on Linux:

```bash
IMAGE=$(base64 -w0 tests/banana-leaf.webp)
curl -X POST http://localhost:8000/api/diagnose \
  -H 'Content-Type: application/json' \
  -d "{\"image_base64\":\"$IMAGE\",\"image_mime_type\":\"image/webp\",\"language\":\"en\"}"
```

Other endpoint examples:

```bash
curl -X POST http://localhost:8000/api/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Should I remove the affected leaves?","language":"en"}'

curl -X POST http://localhost:8000/api/speak \
  -H 'Content-Type: application/json' \
  -d '{"text":"Check the crop again tomorrow.","language":"en"}' \
  -o answer.mp3

curl -G http://localhost:8000/api/speak \
  --data-urlencode 'text=Check the crop again tomorrow.' \
  --data-urlencode 'language=en' -o answer.mp3

curl -X POST http://localhost:8000/api/transcribe \
  -F 'file=@question.webm' -F 'language=en'
```

## Run the tests

```bash
pytest
```

A passing run ends with all tests passing and no network calls. The tests use
mocked provider calls and a no-key environment.

## What works now vs what needs a service

| Feature | Status | Needs |
|---|---|---|
| Text advice | Implemented | A valid Gemma key/model for live calls |
| Image diagnosis | Implemented | A Gemma model confirmed to accept images |
| Knowledge grounding | Implemented | More reviewed entries from Person B |
| Luganda/Swahili output | Implemented | Human quality review |
| Speech-to-text | Generic implemented; Gemma experimental | STT service, or verified Gemma audio support |
| Text-to-speech | Endpoint implemented | Person B's TTS service URL and key |

## Deploy to Render

Create a Render account, connect the GitHub repository, and create the web
service using `render.yaml`. Set the environment variables from the table
above in the Render dashboard. Confirm `/api/health`, then test camera and
microphone access from a phone over the public HTTPS URL. Free instances
sleep, so open the URL once before a demo.

## What I need from you

- [ ] Google AI Studio key in `.env`
- [ ] Exact Gemma 4 model ID in `LLM_MODEL`, confirmed to accept images
- [ ] Whether the Gemma 4 model accepts audio; test `STT_PROVIDER=gemma`
- [ ] Optional OpenRouter key and a Gemma fallback model ID
- [ ] `TTS_API_URL` and key from Person B
- [ ] Organizers' answer on whether non-Gemma STT/TTS tools are allowed
- [ ] A Render or Railway account
- [ ] 8 to 10 real leaf photos in `tests/images/`
- [ ] A Luganda speaker to review Luganda output if possible

## Coordination with Person B

Person B should follow the final request and response shapes in
[`CONTRACT.md`](CONTRACT.md). In particular, send `language`, use `lug` for
Luganda, call `/api/speak` with POST JSON, display `confidence` and
`needs_clearer_photo`, and send the real recording MIME type.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `.env` values ignored | Server started outside the project or stale process | Run from the repo root and restart Uvicorn. |
| 401 or 403 | Invalid key or restricted project | Create a fresh AI Studio key and check project access. |
| 404 model not found | Wrong model ID | Copy the exact Gemma ID from AI Studio. |
| 429 | Provider rate limit | Wait, use the cache, or configure a Gemma fallback. |
| “not configured” | No LLM key is set | Set `LLM_API_KEY` and restart. |
| `ModuleNotFoundError` | Dependencies not installed in `.venv` | Activate `.venv` and rerun the requirements command. |
| Camera or mic blocked | Browser security policy | Use localhost or deployed HTTPS and grant permission. |
| Port already in use | Another server is running | Stop it or run `uvicorn ... --port 8001`. |
| Only Gemma models are allowed | A configured model lacks `gemma` | Correct `LLM_MODEL` and fallback model. |
| Audio not playing | TTS is not configured or browser blocked autoplay | Configure TTS and press Replay. |

## Known limitations

Live Gemma calls and deployment were not verified here without using a key.
Gemma audio input is experimental and unverified. Luganda and Swahili quality
are unverified. The large ONNX file was removed from the git index, but it
still exists in git history; rewriting history was not done.

## Open questions

- Which exact Gemma 4 model ID and image/audio capabilities does the account expose?
- Are non-Gemma speech services permitted by the competition rules?
- Which TTS provider and API contract will Person B supply?
- Which additional reviewed knowledge entries and leaf photos are available?
