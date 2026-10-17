"""
Smoke test: can we generate speech in English, Luganda and Swahili offline?

Setup (do this while you still have good internet, models are downloaded once):
    pip install torch transformers scipy
    # English via Piper:
    pip install piper-tts
    python -m piper.download_voices en_US-lessac-medium

Run:
    python tts_test.py
Then listen to out_en.wav, out_lug.wav, out_sw.wav
"""
import subprocess
import time

import scipy.io.wavfile as wavfile
import torch
from transformers import AutoTokenizer, VitsModel

# Short, farmer-style sentences. Have a Luganda/Swahili speaker check them.
TEXTS = {
    "en": "Your cassava shows signs of brown streak disease. Use clean cuttings next season.",
    "lug": "Emmwanyi zo zirina obulwadde. Genda eri omusomesa w'ebyobulimi.",
    "sw": "Mhogo wako una dalili za ugonjwa wa michirizi ya kahawia. Tumia vipandikizi safi.",
}

MMS_MODELS = {
    "lug": "facebook/mms-tts-lug",
    "sw": "facebook/mms-tts-swh",
}


def tts_piper(text: str, out_path: str) -> None:
    # Piper CLI reads text from stdin
    subprocess.run(
    ["python", "-m", "piper", "-m", "en_US-lessac-medium",
     "--data-dir", "voices", "-f", out_path],
    input=text.encode(),
    check=True,
    )


def tts_mms(lang: str, text: str, out_path: str) -> None:
    name = MMS_MODELS[lang]
    tokenizer = AutoTokenizer.from_pretrained(name)
    model = VitsModel.from_pretrained(name)
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        wav = model(**inputs).waveform[0].numpy()
    wavfile.write(out_path, model.config.sampling_rate, wav)


if __name__ == "__main__":
    for lang, text in TEXTS.items():
        out = f"out_{lang}.wav"
        start = time.time()
        try:
            if lang == "en":
                tts_piper(text, out)
            else:
                tts_mms(lang, text, out)
            print(f"[OK]   {lang}: {out} in {time.time() - start:.1f}s")
        except Exception as e:
            print(f"[FAIL] {lang}: {e}")