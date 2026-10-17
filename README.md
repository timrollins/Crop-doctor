# Crop Doctor

Crop Doctor is a Ugandan crop advice web app for smallholder farmers. A farmer can take a photo or ask by voice, Gemma returns cautious advice grounded in a local knowledge base, and the app can read the answer aloud when audio is configured.

**Project placeholders**

- Team names: `[[TEAM_NAMES]]`
- Live URL: `[[LIVE_URL]]`
- Demo video: `[[DEMO_VIDEO_LINK]]`
- Screenshots: `[[SCREENSHOT_LINK]]`

## How it works

```text
photo or voice
    -> Gemma identifies the likely crop problem
    -> the app checks the local JSON knowledge base
    -> short advice is shown on screen
    -> audio is played when TTS is available
```

## What works now

- Photo diagnosis and typed questions.
- Follow-up questions with the last diagnosis context.
- English, Luganda (`lug`), and Kiswahili (`sw`) UI language selection.
- Client-side photo resizing before upload.
- Voice recording with transcript confirmation.
- Advice history in the browser.
- Audio playback when `TTS_API_URL` is configured, with browser speech fallback when available.
- Static knowledge entries for the current crop problems.

## What depends on configuration

- Gemma diagnosis and advice need the backend model settings from Person A.
- Voice transcription depends on the configured STT provider.
- Server audio depends on the standalone TTS service in `tts_service/`.
- The app needs a deployed HTTPS URL for camera and microphone access on phones.

## Models and tools used

| Component | Purpose | Gemma? | Notes |
|---|---|---|---|
| Gemma model from `LLM_MODEL` | Crop diagnosis and advice | Yes | Exact model ID comes from the backend environment. |
| STT provider from `STT_PROVIDER` | Voice transcription | Maybe | Not Gemma unless the configured provider is Gemma. |
| Meta MMS-TTS | Spoken advice | No | Used by the standalone TTS service; verify model-card licence before commercial use. |
| Optional Piper | Alternate TTS path | No | Not wired by default in this build. |
| FastAPI | Web API and app server | No | Backend framework. |
| Uvicorn | Local/dev server | No | ASGI server. |
| Browser `MediaRecorder` and `speechSynthesis` | Client-side voice capture and fallback playback | No | Browser APIs only. |
| Canvas and FileReader | Client-side photo resizing | No | Keeps uploads smaller before the API call. |

## Licences and credits

| Item | Licence | Notes |
|---|---|---|
| Gemma model | Verify on the exact model card | Check the selected `LLM_MODEL` before any reuse beyond this project. |
| Meta MMS-TTS models | CC-BY-NC 4.0, to the best of our knowledge | Re-check the Hugging Face model cards before any commercial use. |
| FastAPI | MIT | Dependency in the backend and TTS service. |
| Pydantic | MIT | Dependency of FastAPI and the TTS service. |
| Uvicorn | BSD-3-Clause | Local and deployed ASGI server. |
| Transformers | Apache 2.0 | Used in the TTS service. |
| PyTorch | BSD-style / verify | Check the installed wheel and platform build. |
| ffmpeg | Verify | Installed in the TTS Docker image for MP3 encoding. |
| NARO | Intended reference source | Knowledge content should be verified against current recommendations. |
| MAAIF | Intended reference source | Knowledge content should be verified against current recommendations. |
| FAO | Intended reference source | Knowledge content should be verified against current recommendations. |

## Quick start

Read the backend guide first: [RUN_ME_FIRST.md](RUN_ME_FIRST.md).

Backend:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn backend.main:app --reload
```

TTS service:

```bash
cd tts_service
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 7860
```

## Project structure and ownership

- `backend/` and deployment wiring: Person A.
- `frontend/`: Person B.
- `knowledge/`: Person B, with local review still required.
- `tts_service/`: Person B.
- `docs/`: Person B.

## Demo scenarios

### 1. Cassava photo with Luganda audio advice

1. Open the app on a phone.
2. Set the language to `lug`.
3. Take a cassava leaf photo with visible symptoms.
4. Submit the diagnosis.
5. Press play and listen to the Luganda audio if available.

What a good result looks like: the app names cassava brown streak disease or the closest supported problem, shows short practical advice, and the audio button works or the fallback text appears clearly.

### 2. Maize voice question after heavy rain

1. Set the language to English or `sw`.
2. Use the voice button to ask what to do after heavy rain.
3. Confirm the transcript.
4. Send the follow-up.

What a good result looks like: the follow-up is transcribed correctly, the answer mentions maize-relevant advice, and the speaker is told when to seek an officer if needed.

### 3. Fall armyworm photo

1. Switch to English.
2. Capture a maize photo showing whorl damage.
3. Submit the diagnosis.
4. Check that the advice mentions fall armyworm and the confidence badge appears.

What a good result looks like: the app recognises the likely pest, gives low-cost control advice first, and shows whether the photo could be clearer.

## Limitations and ethics

- This is a decision aid, not a diagnosis from an agricultural officer.
- Output quality depends on the photo, the speech transcription, and the knowledge base.
- Luganda and Swahili output need native-speaker review before wider use.
- This version still needs internet for backend, model, and TTS calls.
- The app should not invent pesticide doses or crop facts; when uncertain, it should tell the farmer to ask an extension officer.
- Non-Gemma speech tools are disclosed openly and should only be used if the organizers approve them.

## Next steps

- On-device Gemma for offline use.
- More crops and more local languages.
- A better fine-tuned crop classifier.
- Extension-officer reporting and escalation.
