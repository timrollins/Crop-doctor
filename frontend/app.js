const diagnosisForm = document.querySelector("#diagnosis-form");
const askForm = document.querySelector("#ask-form");
const question = document.querySelector("#question");
const followUp = document.querySelector("#follow-up");
const language = document.querySelector("#language");
const photo = document.querySelector("#photo");
const photoPreview = document.querySelector("#photo-preview");
const status = document.querySelector("#status");
const recordingStatus = document.querySelector("#recording-status");
const retryButton = document.querySelector("#retry-button");
const answer = document.querySelector("#answer");
const answerText = document.querySelector("#answer-text");
const answerAudio = document.querySelector("#answer-audio");
const replayButton = document.querySelector("#replay-button");
const playButton = document.querySelector("#play-button");
const recordButton = document.querySelector("#record-button");
const askRecordButton = document.querySelector("#ask-record-button");
const takePhotoButton = document.querySelector("#take-photo-button");
const clearPhotoButton = document.querySelector("#clear-photo-button");
const retakeButton = document.querySelector("#retake-button");
const resultPhotoWrap = document.querySelector("#result-photo-wrap");
const resultPhoto = document.querySelector("#result-photo");
const resultCrop = document.querySelector("#result-crop");
const resultProblem = document.querySelector("#result-problem");
const confidenceBadge = document.querySelector("#confidence-badge");
const resultWarning = document.querySelector("#result-warning");
const resultDegraded = document.querySelector("#result-degraded");
const audioNote = document.querySelector("#audio-note");
const transcriptPanel = document.querySelector("#transcript-panel");
const transcriptText = document.querySelector("#transcript-text");
const transcriptUseButton = document.querySelector("#transcript-use-button");
const transcriptRerecordButton = document.querySelector("#transcript-rerecord-button");
const historyList = document.querySelector("#history-list");
const goDiagnoseButton = document.querySelector("#go-diagnose");
const goAskButton = document.querySelector("#go-ask");
const diagnosisSection = document.querySelector("#diagnosis-section");
const askSection = document.querySelector("#ask-section");

const STORAGE_LANGUAGE_KEY = "crop-doctor-language";
const STORAGE_HISTORY_KEY = "crop-doctor-history";
const MAX_HISTORY = 5;

let previewUrl = "";
let currentAudioUrl = "";
let currentAdvice = "";
let currentProblemId = "";
let retryAction = null;
let serviceState = {
  ttsConfigured: true,
  sttConfigured: true,
};
const recordingSessions = new WeakMap();
let transcriptState = {
  text: "",
  targetInput: null,
  triggerButton: null,
};

const actionButtons = [
  goDiagnoseButton,
  goAskButton,
  recordButton,
  askRecordButton,
  playButton,
  replayButton,
  takePhotoButton,
  clearPhotoButton,
  retakeButton,
  transcriptUseButton,
  transcriptRerecordButton,
  diagnosisForm.querySelector('button[type="submit"]'),
  askForm.querySelector('button[type="submit"]'),
];

function safeReadStorage(key, fallback) {
  try {
    const value = window.localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function safeWriteStorage(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    return;
  }
}

function setLanguage(code) {
  const nextLanguage = code || "en";
  language.value = nextLanguage;
  document.documentElement.lang = nextLanguage;
  safeWriteStorage(STORAGE_LANGUAGE_KEY, nextLanguage);
}

function setStatus(message, retry = null) {
  status.textContent = message;
  retryAction = retry;
  retryButton.hidden = !retry;
}

function setRecordingStatus(message) {
  recordingStatus.textContent = message;
}

function setBusy(isBusy) {
  actionButtons.forEach((button) => {
    if (button) {
      button.disabled = isBusy;
    }
  });
}

function focusSection(section) {
  if (section) {
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function confidenceLabel(level) {
  if (level === "high") return "High confidence";
  if (level === "medium") return "Medium confidence";
  return "Low confidence";
}

function setConfidenceBadge(level) {
  confidenceBadge.textContent = confidenceLabel(level);
  confidenceBadge.className = "confidence-badge";
  confidenceBadge.classList.add(level === "high" ? "badge-high" : level === "medium" ? "badge-medium" : "badge-low");
}

function clearResultAudio() {
  if (currentAudioUrl) {
    URL.revokeObjectURL(currentAudioUrl);
    currentAudioUrl = "";
  }
  answerAudio.removeAttribute("src");
  answerAudio.hidden = true;
  answerAudio.load();
}

function setPhotoPreview(url) {
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
  }
  previewUrl = url;
  photoPreview.src = url;
  photoPreview.hidden = false;
}

function clearPhotoSelection() {
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
    previewUrl = "";
  }
  photo.value = "";
  photoPreview.removeAttribute("src");
  photoPreview.hidden = true;
}

function loadHistory() {
  const stored = safeReadStorage(STORAGE_HISTORY_KEY, []);
  return Array.isArray(stored) ? stored : [];
}

function saveHistory(entries) {
  safeWriteStorage(STORAGE_HISTORY_KEY, entries.slice(0, MAX_HISTORY));
}

function renderHistory() {
  const entries = loadHistory();
  historyList.replaceChildren();

  if (!entries.length) {
    const emptyItem = document.createElement("li");
    emptyItem.className = "note";
    emptyItem.textContent = "No advice yet. Your last five results will appear here.";
    historyList.appendChild(emptyItem);
    return;
  }

  entries.forEach((entry) => {
    const listItem = document.createElement("li");
    listItem.className = "history-item";

    const button = document.createElement("button");
    button.type = "button";
    button.addEventListener("click", () => {
      renderResult(entry, false, "");
      setStatus(`Showing saved advice for ${entry.problem || "this crop"}.`);
      focusSection(answer);
    });

    const title = document.createElement("span");
    title.className = "history-item-title";
    title.textContent = `${entry.crop || "Crop"} - ${entry.problem || "Advice"}`;

    const meta = document.createElement("span");
    meta.className = "history-item-meta";
    const time = entry.timestamp ? new Date(entry.timestamp).toLocaleString() : "Earlier";
    meta.textContent = `${time} • ${confidenceLabel(entry.confidence || "low")}`;

    button.append(title, meta);
    listItem.appendChild(button);
    historyList.appendChild(listItem);
  });
}

function addHistoryEntry(data) {
  const entry = {
    timestamp: new Date().toISOString(),
    language: data.language || language.value,
    crop: data.crop || "",
    problem: data.problem_name || "",
    problem_id: data.problem_id || "",
    confidence: data.confidence || "low",
    answer: data.answer || data.advice_text || "",
    needs_clearer_photo: Boolean(data.needs_clearer_photo),
    degraded: Boolean(data.degraded),
  };

  const entries = loadHistory();
  entries.unshift(entry);
  saveHistory(entries.slice(0, MAX_HISTORY));
  renderHistory();
}

function showTranscript(text, targetInput, triggerButton) {
  transcriptState = {
    text,
    targetInput,
    triggerButton,
  };
  transcriptText.textContent = `I heard: ${text}`;
  transcriptPanel.hidden = false;
  setRecordingStatus("Review the transcript, then use it or record again.");
  focusSection(transcriptPanel);
}

function hideTranscript() {
  transcriptPanel.hidden = true;
  transcriptText.textContent = "";
}

function resetTranscriptContext() {
  transcriptState = {
    text: "",
    targetInput: null,
    triggerButton: null,
  };
  hideTranscript();
}

function getPreferredRecorderMimeType() {
  const candidates = [
    "audio/mp4;codecs=mp4a.40.2",
    "audio/mp4",
    "audio/aac",
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/ogg",
  ];
  return candidates.find((candidate) => window.MediaRecorder && MediaRecorder.isTypeSupported(candidate)) || "";
}

function getFileExtension(mimeType) {
  if (mimeType.includes("mp4") || mimeType.includes("aac")) return "m4a";
  if (mimeType.includes("ogg")) return "ogg";
  return "webm";
}

function fileToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      resolve(result.split(",", 2)[1] || "");
    };
    reader.onerror = () => reject(new Error("The image could not be read."));
    reader.readAsDataURL(blob);
  });
}

function loadImage(url) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("The image could not be loaded."));
    image.src = url;
  });
}

async function resizeImageFile(file) {
  const sourceUrl = URL.createObjectURL(file);
  try {
    const image = await loadImage(sourceUrl);
    const maxSide = 768;
    const scale = Math.min(1, maxSide / Math.max(image.width, image.height));
    const width = Math.max(1, Math.round(image.width * scale));
    const height = Math.max(1, Math.round(image.height * scale));

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;

    const context = canvas.getContext("2d");
    if (!context) {
      throw new Error("Your browser cannot prepare the photo.");
    }

    context.drawImage(image, 0, 0, width, height);

    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob((value) => {
        if (!value) {
          reject(new Error("The photo could not be resized."));
          return;
        }
        resolve(value);
      }, "image/jpeg", 0.8);
    });

    const base64 = await fileToBase64(blob);
    return {
      image_base64: base64,
      image_mime_type: blob.type || "image/jpeg",
    };
  } finally {
    URL.revokeObjectURL(sourceUrl);
  }
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const message = response.status === 429
      ? "The advisor is busy, please try again in a minute."
      : response.status === 502
        ? "We couldn't reach the advisor, check your signal and try again."
        : response.status === 422
          ? "Please check the question or photo and try again."
          : "The request failed. Please try again.";
    throw new Error(message);
  }

  return response.json();
}

async function attemptBrowserSpeech(text) {
  const synth = window.speechSynthesis;
  if (!synth || !window.SpeechSynthesisUtterance) {
    return false;
  }

  const voices = synth.getVoices();
  const wanted = language.value === "sw" ? ["sw-KE", "sw"] : language.value === "lug" ? ["lg", "lug"] : ["en"];
  const voice = voices.find((item) => wanted.some((prefix) => item.lang && item.lang.toLowerCase().startsWith(prefix.toLowerCase())));

  if (!voice) {
    return false;
  }

  synth.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = voice.lang || language.value;
  utterance.voice = voice;
  synth.speak(utterance);
  return true;
}

async function speakAdvice(text) {
  currentAdvice = text;
  clearResultAudio();
  audioNote.hidden = true;

  if (!text) {
    return;
  }

  if (serviceState.ttsConfigured) {
    try {
      setStatus("Preparing audio…");
      const response = await fetch("/api/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, language: language.value }),
      });

      if (!response.ok) {
        throw new Error("Audio is not available right now.");
      }

      const blob = await response.blob();
      currentAudioUrl = URL.createObjectURL(blob);
      answerAudio.src = currentAudioUrl;
      answerAudio.hidden = false;
      await answerAudio.play().catch(() => {});
      setStatus("");
      return;
    } catch {
      clearResultAudio();
    }
  }

  const browserVoiceUsed = await attemptBrowserSpeech(text);
  if (!browserVoiceUsed) {
    audioNote.textContent = "Audio is not available. Read the advice below.";
    audioNote.hidden = false;
  }
  setStatus("");
}

function renderResult(data, includeAudio = true, photoUrl = previewUrl) {
  const adviceText = data.answer || data.advice_text || "";
  currentAdvice = adviceText;
  currentProblemId = data.problem_id || "";

  answer.hidden = false;
  resultPhotoWrap.hidden = !photoUrl;
  if (photoUrl) {
    resultPhoto.src = photoUrl;
  }
  resultCrop.textContent = data.crop ? `Crop: ${data.crop}` : "";
  resultProblem.textContent = data.problem_name ? `Problem: ${data.problem_name}` : "";
  answerText.textContent = adviceText;
  setConfidenceBadge(data.confidence || "low");

  if (data.needs_clearer_photo) {
    resultWarning.textContent = "Take a closer photo in daylight, showing both sides of the leaf.";
    resultWarning.hidden = false;
    retakeButton.hidden = false;
  } else {
    resultWarning.hidden = true;
    resultWarning.textContent = "";
    retakeButton.hidden = true;
  }

  if (data.degraded) {
    resultDegraded.textContent = "This advice is simplified because the signal, photo, or model confidence was limited.";
    resultDegraded.hidden = false;
  } else {
    resultDegraded.hidden = true;
    resultDegraded.textContent = "";
  }

  if (includeAudio) {
    void speakAdvice(adviceText);
  } else if (!serviceState.ttsConfigured) {
    audioNote.textContent = "Audio is not available. Read the advice below.";
    audioNote.hidden = false;
  }

  focusSection(answer);
}

async function diagnoseCrop() {
  if (!navigator.onLine) {
    throw new Error("You are offline. Check your signal and try again.");
  }

  const file = photo.files[0];
  const typedQuestion = question.value.trim();

  if (!file && !typedQuestion) {
    throw new Error("Take a photo or type a question before checking the crop.");
  }

  const body = { language: language.value };
  if (typedQuestion) {
    body.question = typedQuestion;
  }
  if (file) {
    Object.assign(body, await resizeImageFile(file));
  }

  setStatus("Looking at your crop…");
  const data = await postJson("/api/diagnose", body);
  renderResult(data, true, previewUrl);
  addHistoryEntry(data);
  setStatus("");
}

async function askFollowUp() {
  if (!navigator.onLine) {
    throw new Error("You are offline. Check your signal and try again.");
  }

  const text = followUp.value.trim();
  if (!text) {
    throw new Error("Ask a question before sending the follow-up.");
  }

  setStatus("Writing your advice…");
  const body = {
    question: text,
    language: language.value,
  };

  if (currentProblemId) {
    body.problem_id = currentProblemId;
  }

  const data = await postJson("/api/ask", body);
  renderResult(data, true, previewUrl);
  addHistoryEntry(data);
  setStatus("");
}

async function runAction(action) {
  setBusy(true);
  setStatus("");
  try {
    await action();
    retryButton.hidden = true;
    retryAction = null;
  } catch (error) {
    const message = error instanceof Error ? error.message : "The request failed. Please try again.";
    setStatus(message, action);
  } finally {
    setBusy(false);
  }
}

function startRecording(targetInput, triggerButton) {
  if (!serviceState.sttConfigured) {
    setRecordingStatus("Voice recording is not available right now.");
    return;
  }

  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    setRecordingStatus("Recording is not supported on this device.");
    return;
  }

  const existingSession = recordingSessions.get(triggerButton);
  if (existingSession?.recorder?.state === "recording") {
    existingSession.recorder.stop();
    return;
  }

  const originalLabel = triggerButton.textContent;
  const mimeType = getPreferredRecorderMimeType();
  const session = {
    chunks: [],
    recorder: null,
    stream: null,
    timeoutId: null,
    originalLabel,
  };
  recordingSessions.set(triggerButton, session);

  const finishRecording = () => {
    if (session.timeoutId) {
      window.clearTimeout(session.timeoutId);
    }
    if (session.stream) {
      session.stream.getTracks().forEach((track) => track.stop());
    }
    triggerButton.dataset.recording = "false";
    triggerButton.setAttribute("aria-pressed", "false");
    triggerButton.textContent = session.originalLabel;
    recordingSessions.delete(triggerButton);
  };

  const start = async () => {
    try {
      session.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      session.recorder = mimeType ? new MediaRecorder(session.stream, { mimeType }) : new MediaRecorder(session.stream);
      triggerButton.dataset.recording = "true";
      triggerButton.setAttribute("aria-pressed", "true");
      triggerButton.textContent = "⏹ Stop recording";
      setRecordingStatus("Listening... tap stop or wait 30 seconds.");

      session.recorder.addEventListener("dataavailable", (event) => {
        if (event.data.size) {
          session.chunks.push(event.data);
        }
      });

      session.recorder.addEventListener("stop", async () => {
        finishRecording();
        if (!session.chunks.length) {
          setRecordingStatus("No speech was captured. Try again.");
          return;
        }

        setRecordingStatus("Transcribing…");
        try {
          const audioBlob = new Blob(session.chunks, { type: session.recorder.mimeType || mimeType || "audio/webm" });
          const formData = new FormData();
          formData.append("file", audioBlob, `recording.${getFileExtension(audioBlob.type || mimeType || "audio/webm")}`);
          const response = await fetch(`/api/transcribe?language=${encodeURIComponent(language.value)}`, {
            method: "POST",
            body: formData,
          });

          if (!response.ok) {
            if (response.status === 502) {
              throw new Error("We couldn't transcribe the audio right now.");
            }
            throw new Error("The recording could not be transcribed.");
          }

          const data = await response.json();
          const transcript = String(data.text || "").trim();
          if (!transcript) {
            throw new Error("We didn't catch any speech. Try again.");
          }

          showTranscript(transcript, targetInput, triggerButton);
        } catch (error) {
          setRecordingStatus(error instanceof Error ? error.message : "The recording could not be transcribed.");
        }
      });

      session.timeoutId = window.setTimeout(() => {
        if (session.recorder?.state === "recording") {
          session.recorder.stop();
        }
      }, 30000);

      session.recorder.start();
    } catch {
      finishRecording();
      setRecordingStatus("Microphone permission was not granted.");
    }
  };

  void start();
}

function updateServiceStatus() {
  if (!serviceState.ttsConfigured) {
    audioNote.textContent = "Audio is not available from the server, so the app will try your device voice or show the text only.";
    audioNote.hidden = false;
  } else {
    audioNote.hidden = true;
    audioNote.textContent = "";
  }

  recordButton.disabled = !serviceState.sttConfigured;
  askRecordButton.disabled = !serviceState.sttConfigured;
  if (!serviceState.sttConfigured) {
    setRecordingStatus("Voice recording is not available right now.");
  }
}

async function loadServiceStatus() {
  try {
    const response = await fetch("/api/status");
    if (!response.ok) {
      return;
    }
    const data = await response.json();
    serviceState.ttsConfigured = Boolean(data.tts_configured);
    serviceState.sttConfigured = Boolean(data.stt_configured);
  } catch {
    return;
  } finally {
    updateServiceStatus();
  }
}

language.addEventListener("change", () => setLanguage(language.value));

goDiagnoseButton.addEventListener("click", () => {
  focusSection(diagnosisSection);
  photo.focus();
});

goAskButton.addEventListener("click", () => {
  focusSection(askSection);
  followUp.focus();
});

photo.addEventListener("change", () => {
  const file = photo.files[0];
  if (!file) {
    clearPhotoSelection();
    return;
  }
  setPhotoPreview(URL.createObjectURL(file));
});

takePhotoButton.addEventListener("click", () => {
  photo.click();
});

clearPhotoButton.addEventListener("click", () => {
  clearPhotoSelection();
});

retakeButton.addEventListener("click", () => {
  focusSection(diagnosisSection);
  photo.click();
});

diagnosisForm.addEventListener("submit", (event) => {
  event.preventDefault();
  void runAction(diagnoseCrop);
});

askForm.addEventListener("submit", (event) => {
  event.preventDefault();
  void runAction(askFollowUp);
});

recordButton.addEventListener("click", () => {
  startRecording(question, recordButton);
});

askRecordButton.addEventListener("click", () => {
  startRecording(followUp, askRecordButton);
});

transcriptUseButton.addEventListener("click", () => {
  if (!transcriptState.targetInput) {
    return;
  }
  const targetInput = transcriptState.targetInput;
  targetInput.value = transcriptState.text;
  resetTranscriptContext();
  targetInput.focus();
});

transcriptRerecordButton.addEventListener("click", () => {
  if (!transcriptState.targetInput || !transcriptState.triggerButton) {
    resetTranscriptContext();
    return;
  }
  const targetInput = transcriptState.targetInput;
  const triggerButton = transcriptState.triggerButton;
  resetTranscriptContext();
  startRecording(targetInput, triggerButton);
});

retryButton.addEventListener("click", () => {
  if (retryAction) {
    void runAction(retryAction);
  }
});

playButton.addEventListener("click", () => {
  if (currentAdvice) {
    void speakAdvice(currentAdvice);
  }
});

replayButton.addEventListener("click", () => {
  if (currentAudioUrl) {
    answerAudio.currentTime = 0;
    void answerAudio.play().catch(() => {});
    return;
  }
  if (currentAdvice) {
    void speakAdvice(currentAdvice);
  }
});

answerAudio.addEventListener("ended", () => {
  answerAudio.currentTime = 0;
});

setLanguage(safeReadStorage(STORAGE_LANGUAGE_KEY, "en"));
renderHistory();
void loadServiceStatus();
