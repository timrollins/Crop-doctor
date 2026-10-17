# Crop Doctor API contract

## `GET /api/health`

Returns `{ "status": "ok" }`.

## `POST /api/diagnose`

Request JSON:

```json
{"question": "My tomato leaves have brown spots", "problem_id": "leaf-spot"}
```

`question` is required. `problem_id` is optional and resolves to
`knowledge/<problem_id>.json`. For an image, add `image_base64` and its
`image_mime_type`. The response contains `answer` and the resolved `problem`
(or `null`).

## `POST /api/ask`

Request JSON: `{"question": "Should I remove the spotted leaves?", "language": "en"}`.
The answer is kept short for follow-up questions and audio playback.

## `POST /api/transcribe`

Multipart upload with a `file` field. Returns `{ "text": "..." }`.
Requires `STT_API_URL`.

## `POST /api/speak`

Accepts a `text` query parameter and returns an MP3. Requires `TTS_API_URL`.
