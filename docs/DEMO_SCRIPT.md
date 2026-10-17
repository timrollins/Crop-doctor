# Demo Script

## 2-minute narration

**0:00 - 0:15**

Crop Doctor helps Ugandan smallholder farmers get short crop advice from a photo or a voice question. It uses Gemma for diagnosis, then checks a local knowledge base for the response.

**0:15 - 0:35**

I’ll start with a cassava leaf photo in Luganda. The app resizes the image first, sends it to the backend, and shows the advice with a confidence badge.

**0:35 - 0:55**

Next I’ll ask a maize question by voice after heavy rain. You can see the transcript before I send it, so I can correct transcription errors before the answer comes back.

**0:55 - 1:15**

Now I’ll show a fall armyworm photo in maize. The app shows the problem name, the crop, the advice, and the audio controls. If audio is configured, it plays the answer aloud.

**1:15 - 1:35**

The history list keeps the last five results in the browser, and the follow-up box keeps the last diagnosis context so farmers can ask what to do next.

**1:35 - 2:00**

This is a decision aid, not a replacement for an agricultural extension officer. The knowledge base is still being reviewed with NARO, MAAIF, and FAO references.

## Backup plan if the live API or TTS is down

- Show the static frontend and the knowledge base structure.
- Walk through the docs and the test checklist.
- Use screenshots of the three demo scenarios instead of live requests.
- Explain that the backend and TTS are separate services and point to the expected env vars.
- If audio is down, keep the text result and mention that browser speech fallback may still work locally.
