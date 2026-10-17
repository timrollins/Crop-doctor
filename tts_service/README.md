# Crop Doctor TTS Service

Standalone text-to-speech service for Crop Doctor. The main app calls this service with `POST /synthesize` or `POST /` and expects MP3 bytes back.

## Local run

```bash
cd tts_service
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 7860
```

If you set `TTS_SERVICE_TOKEN`, send the same value in `Authorization: Bearer ...`.

## Quick test

```bash
curl -X POST http://127.0.0.1:7860/synthesize \
  -H 'Content-Type: application/json' \
  -d '{"text":"Crop Doctor is ready.","language":"en"}' \
  --output answer.mp3
```

The saved file should be an `.mp3` you can play in a browser or media player.

## Docker build and run

```bash
cd tts_service
docker build -t crop-doctor-tts .
docker run --rm -p 7860:7860 -e TTS_SERVICE_TOKEN=change-me crop-doctor-tts
```

## Hugging Face Spaces deployment

1. Create a new Hugging Face Space and choose the Docker SDK.
2. Upload or push the `tts_service/` folder contents as the Space source.
3. Set `TTS_SERVICE_TOKEN` as a secret in the Space settings if you want auth.
4. Make sure the Space uses port `7860`.
5. After deployment, copy the Space URL into the main app as `TTS_API_URL`.

## Notes on models and hosting

- This service lazily downloads the MMS-TTS model weights the first time each language is used, so the first request may be slow.
- You can prefetch models during image build if you want faster first use, but that makes the Docker image much larger.
- Free hosting can sleep between requests, so plan for a slower first call after idle time.
- Memory use and first-request timing are to be measured in the actual deployment environment.
