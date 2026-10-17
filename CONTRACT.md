# Crop Doctor API contract

Language codes are `en`, `lug`, and `sw`. The aliases `lg`, `swa`, and
`kiswahili` are accepted and normalised to `lug` or `sw`.

## Health and status

`GET /api/health` returns exactly `{"status":"ok"}`.

`GET /api/status` returns non-secret configuration and knowledge counts:

```json
{"llm_configured": true, "model": "gemma-model-id", "fallback_configured": false,
"stt_provider": "generic", "stt_configured": false, "tts_configured": false,
"knowledge_entries": 4, "cache_seconds": 0}
```

## Diagnosis

`POST /api/diagnose` accepts `question` (optional), `language` (default `en`),
optional `problem_id`, and optional `image_base64` plus `image_mime_type`.
At least one of question, image, or problem ID is required. The response
contains the backward-compatible `answer` and `problem` fields plus:
`advice_text`, `problem_id`, `problem_name`, `crop`, `confidence`, `language`,
`needs_clearer_photo`, and `degraded`.

## Follow-up

`POST /api/ask` accepts `question`, `language`, and optional `problem_id`.
It returns the same response shape; diagnosis-only fields are null or default.

## Speech

`POST /api/transcribe` accepts a multipart `file` and optional `language`
query field. It returns `{"text":"..."}`.

`POST /api/speak` accepts JSON `{"text":"...", "language":"en"}` and returns
audio. The compatibility route `GET /api/speak?text=...&language=en` remains
available.

Invalid language or input returns 422. Provider rate limits return 429.
Other provider failures return 502.

## Changes Person B must make in the frontend

Send `language` with diagnosis and use `lug` for Luganda. Call `/api/speak`
with POST JSON. Show `confidence` and `needs_clearer_photo`. Send the actual
recording MIME type to `/api/transcribe`.
