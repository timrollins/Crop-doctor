# Manual Testing Checklist

Use this on Android Chrome and iPhone Safari. Mark each row after testing.

| Test | Android Chrome | iPhone Safari | Pass | Fail | Notes |
|---|---|---|---|---|---|
| Open the app and confirm the language selector appears at the top | [ ] | [ ] | [ ] | [ ] | |
| Set English, Luganda, and Kiswahili one by one | [ ] | [ ] | [ ] | [ ] | |
| Check crop with photo only, no typed question | [ ] | [ ] | [ ] | [ ] | |
| Take a fresh camera photo through the app | [ ] | [ ] | [ ] | [ ] | |
| Ask a question by voice and confirm the transcript before sending | [ ] | [ ] | [ ] | [ ] | |
| Play advice and then use Replay | [ ] | [ ] | [ ] | [ ] | |
| Slow connection test: load, wait, and retry once | [ ] | [ ] | [ ] | [ ] | |
| Trigger 429 busy and confirm the friendly message | [ ] | [ ] | [ ] | [ ] | |
| Trigger 502 provider failure and confirm the friendly message | [ ] | [ ] | [ ] | [ ] | |
| Capture a low-confidence photo and confirm the clearer-photo hint | [ ] | [ ] | [ ] | [ ] | |
| Confirm BXW wording says to report to the agricultural officer | [ ] | [ ] | [ ] | [ ] | |
| Run the cassava photo scenario once | [ ] | [ ] | [ ] | [ ] | |
| Run the maize voice-question scenario once | [ ] | [ ] | [ ] | [ ] | |
| Run the fall armyworm photo scenario once | [ ] | [ ] | [ ] | [ ] | |
| Run the cassava photo scenario a second time | [ ] | [ ] | [ ] | [ ] | |
| Run the maize voice-question scenario a second time | [ ] | [ ] | [ ] | [ ] | |
| Run the fall armyworm photo scenario a second time | [ ] | [ ] | [ ] | [ ] | |

## Scenario notes

- Cassava photo: expect a cassava problem, a confidence badge, and a useful next step.
- Maize voice question: expect the transcript to appear before sending, then a maize-related answer.
- Fall armyworm photo: expect the advice to mention the pest and low-cost controls first.
