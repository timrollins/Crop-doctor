# Crop Doctor API contract

## `GET /api/health`

Returns `{ "status": "ok" }`.

## `POST /api/diagnose`

Request JSON:

```json
{"question": "My tomato leaves have brown spots", "problem_id": "leaf-spot"}
```

`question` is required. `problem_id` is optional and resolves to
`knowledge/<problem_id>.json`. The response contains `answer` and the resolved
`problem` (or `null`).

## `POST /api/transcribe`

Multipart upload with a `file` field. Returns `{ "text": "..." }`.
Requires `STT_API_URL`.

## `POST /api/speak`

Accepts a `text` query parameter and returns an MP3. Requires `TTS_API_URL`.
