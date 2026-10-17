# Person B Guide

This guide covers the frontend, knowledge base, and standalone TTS service.

## 1) Run everything locally

The project path has spaces, so quote it. On this machine the repo is at `C:\Users\ADMIN\Desktop\Crop-doctor`; if you are following the original setup path, use `~\"hacking for good\"\Crop-doctor` with quotes around the folder that contains spaces.

Backend:

```bash
cd "C:\Users\ADMIN\Desktop\Crop-doctor"
python -m venv .venv
. .venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn backend.main:app --reload
```

TTS service in a second terminal:

```bash
cd "C:\Users\ADMIN\Desktop\Crop-doctor\tts_service"
python -m venv .venv
. .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload --port 7860
```

Set the backend env vars before you test audio:

```bash
set TTS_API_URL=http://127.0.0.1:7860/synthesize
set TTS_API_KEY=
```

If you protect the TTS service with a token, set the same value in `TTS_SERVICE_TOKEN` for the service and `TTS_API_KEY` for the backend.

## 2) Deploy the TTS service

1. Create a Hugging Face account.
2. Create a new Space and choose the Docker SDK.
3. Push or upload the contents of `tts_service/`.
4. Set `TTS_SERVICE_TOKEN` as a secret if you want auth.
5. Wait for the Space build to finish.
6. Copy the deployed Space URL and hand it to Person A as `TTS_API_URL`.
7. If the Space is protected, also hand over the shared secret as `TTS_API_KEY`.

## 3) What I need from you

- [ ] Hugging Face account for the TTS Space.
- [ ] Deployed `TTS_API_URL` and matching token, if used.
- [ ] A native Luganda speaker to review `name_lug` and spoken output.
- [ ] A Swahili speaker to review `name_sw` and spoken output.
- [ ] Verification of every item in the facts list below against NARO, MAAIF, or FAO.
- [ ] Screenshots and a short demo video.
- [ ] Team names and the live URL.
- [ ] The organizers' answer on whether non-Gemma speech tools are allowed.

## 4) Facts to verify

- `banana_bxw`: BXW is reportable and the agricultural officer should be contacted quickly.
- `cassava_cbsd`: current recommended cassava varieties and clean planting material advice.
- `banana_black_sigatoka`: whether the sanitation and registered fungicide advice matches current Uganda guidance.
- `maize_mln`: the wording that MLN needs rapid reporting and no chemical cure.
- `coffee_wilt_disease`: the tree-destruction and reporting advice.
- `coffee_leaf_rust`: whether the shade, pruning, and registered product advice is current.
- `bean_rust`: whether the bean rust control advice needs changes for your area.
- `tomato_late_blight`: whether the product examples should stay as written.
- `maize_fall_armyworm`: whether the named active ingredient and cultural steps are the current recommendation.
- `maize_gray_leaf_spot`: whether this entry should stay in the first release or be removed.

## 5) Open questions

- Whether the organizers approve non-Gemma STT/TTS components.
- Whether the TTS service should stay MMS-TTS only or add Piper later.
- Whether Luganda and Swahili names should be filled only after native-speaker review.
- Whether any of the draft knowledge entries should be removed before the demo.
- Whether the backend should expose any more status flags for the frontend.
- Whether the production TTS deployment will use a secret token or stay open.

## 6) Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Audio won't play on iPhone | Autoplay blocked after async work or the TTS service is unavailable | Press Play, then Replay if needed, and check `TTS_API_URL`. |
| Mic permission denied | Browser permission was blocked | Re-enable microphone access in the site settings and try again. |
| Camera blocked | The page is not served over HTTPS | Use the deployed HTTPS URL or localhost during development. |
| TTS service times out on the first call | Models are still loading or the host slept | Wait for warm-up, keep the Space alive, and try again. |
| 502 from `/api/speak` | Backend cannot reach the TTS service | Check `TTS_API_URL`, the service logs, and any auth token mismatch. |
| Wrong language audio | The wrong language code was sent or the fallback voice was chosen | Confirm `en`, `lug`, or `sw` and re-test the language selector. |
| Images too large | The user uploaded a full-size photo | Let the app resize it, or retake the photo closer to the leaf. |
