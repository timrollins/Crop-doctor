const form = document.querySelector("#diagnosis-form");
const askForm = document.querySelector("#ask-form");
const question = document.querySelector("#question");
const followUp = document.querySelector("#follow-up");
const language = document.querySelector("#language");
const photo = document.querySelector("#photo");
const photoPreview = document.querySelector("#photo-preview");
const status = document.querySelector("#status");
const recordingStatus = document.querySelector("#recording-status");
const answer = document.querySelector("#answer");
const answerText = document.querySelector("#answer-text");
const answerAudio = document.querySelector("#answer-audio");
const replayButton = document.querySelector("#replay-button");
const recordButton = document.querySelector("#record-button");
const askRecordButton = document.querySelector("#ask-record-button");

let lastAudioUrl = "";

function setStatus(message) {
  status.textContent = message;
}

async function speak(text) {
  if (lastAudioUrl) URL.revokeObjectURL(lastAudioUrl);
  const response = await fetch(`/api/speak?text=${encodeURIComponent(text)}`);
  if (!response.ok) throw new Error("Audio is not available right now.");
  const blob = await response.blob();
  lastAudioUrl = URL.createObjectURL(blob);
  answerAudio.src = lastAudioUrl;
  answerAudio.hidden = false;
  await answerAudio.play().catch(() => {});
}

function showAnswer(text) {
  answerText.textContent = text;
  answer.hidden = false;
}

function imageAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1]);
    reader.onerror = () => reject(new Error("The photo could not be read."));
    reader.readAsDataURL(file);
  });
}

async function submitAnswer(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error("The request failed. Please try again.");
  return response.json();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Looking at your crop...");
  answer.hidden = true;
  try {
    const body = { question: question.value };
    if (photo.files[0]) {
      body.image_base64 = await imageAsBase64(photo.files[0]);
      body.image_mime_type = photo.files[0].type || "image/jpeg";
    }
    const data = await submitAnswer("/api/diagnose", body);
    showAnswer(data.answer);
    setStatus("");
    try {
      await speak(data.answer);
    } catch {
      setStatus("Advice is ready. Audio is unavailable.");
    }
  } catch (error) {
    setStatus(error.message);
  }
});

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Preparing your answer...");
  try {
    const data = await submitAnswer("/api/ask", {
      question: followUp.value,
      language: language.value,
    });
    showAnswer(data.answer);
    setStatus("");
    try {
      await speak(data.answer);
    } catch {
      setStatus("Answer is ready. Audio is unavailable.");
    }
  } catch (error) {
    setStatus(error.message);
  }
});

photo.addEventListener("change", () => {
  const file = photo.files[0];
  if (!file) {
    photoPreview.hidden = true;
    return;
  }
  photoPreview.src = URL.createObjectURL(file);
  photoPreview.hidden = false;
});

function setupRecorder(button, target) {
  let recorder;
  let chunks = [];
  button.addEventListener("click", async () => {
    if (recorder?.state === "recording") {
      recorder.stop();
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      recordingStatus.textContent = "Recording is not supported on this device.";
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recorder = new MediaRecorder(stream);
      chunks = [];
      recorder.addEventListener("dataavailable", (event) => chunks.push(event.data));
      recorder.addEventListener("stop", async () => {
        stream.getTracks().forEach((track) => track.stop());
        button.textContent = button === recordButton ? "🎙️ Record question" : "🎙️";
        button.setAttribute("aria-pressed", "false");
        recordingStatus.textContent = "Transcribing...";
        try {
          const audio = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
          const formData = new FormData();
          formData.append("file", audio, "question.webm");
          const response = await fetch("/api/transcribe", { method: "POST", body: formData });
          if (!response.ok) throw new Error("The recording could not be transcribed.");
          target.value = (await response.json()).text;
          recordingStatus.textContent = "Transcription ready.";
        } catch (error) {
          recordingStatus.textContent = error.message;
        }
      });
      recorder.start();
      button.textContent = button === recordButton ? "⏹️ Stop recording" : "⏹️";
      button.setAttribute("aria-pressed", "true");
      recordingStatus.textContent = "Listening...";
    } catch {
      recordingStatus.textContent = "Microphone permission was not granted.";
    }
  });
}

setupRecorder(recordButton, question);
setupRecorder(askRecordButton, followUp);

replayButton.addEventListener("click", () => {
  if (answerAudio.src) {
    answerAudio.currentTime = 0;
    answerAudio.play().catch(() => {});
  }
});
