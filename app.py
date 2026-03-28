import os
import wave
import numpy as np
from flask import Flask, request, jsonify, render_template

from scipy.signal import butter, filtfilt, hilbert
from scipy.stats import kurtosis

from features import extract_advanced_features

app = Flask(__name__)


class EngineAnalyzer:

    # 🔹 Фильтр (убираем низ и лишний шум)
    def bandpass_filter(self, audio, sr, low=300, high=4000):
        nyq = 0.5 * sr
        b, a = butter(4, [low / nyq, high / nyq], btype='band')
        return filtfilt(b, a, audio)

    # 🔹 Огибающая (для поиска ударов)
    def compute_envelope(self, audio):
        analytic = hilbert(audio)
        return np.abs(analytic)

    def process(self, audio, sr=22050):

        # 🔹 1. Проверка сигнала
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < 0.02:
            return {
                "type": "low_signal",
                "rpm": 0,
                "confidence": 1.0,
                "recommendation": "Запись слишком тихая. Поднесите телефон ближе к двигателю."
            }

        # 🔹 2. Фильтрация
        filtered = self.bandpass_filter(audio, sr)

        # 🔹 3. Извлечение фич
        feats = extract_advanced_features(filtered, sr)

        # 🔹 4. Kurtosis (главный индикатор стука)
        k = kurtosis(filtered)

        # 🔹 5. Envelope пики (удары)
        env = self.compute_envelope(filtered)
        peak_count = np.sum(env > (np.mean(env) + 2 * np.std(env)))

        # 🔹 6. Spectral Flux
        flux = feats["flux_mean"]

        # 🔹 7. FFT → RPM
        freqs = np.fft.rfftfreq(len(audio), d=1 / sr)
        amps = np.abs(np.fft.rfft(audio))

        low_zone = (freqs >= 15) & (freqs <= 50)
        if np.any(low_zone):
            base_freq = freqs[low_zone][np.argmax(amps[low_zone])]
            rpm = int((base_freq * 60) / 2)
        else:
            rpm = 800

        # 🔥 СКОРИНГ

        # --- Стук (гидрики / клапана)
        score_knock = 0
        score_knock += min(k / 10, 0.4)
        score_knock += min(flux / 5, 0.3)
        score_knock += min(peak_count / 500, 0.3)

        # --- Свист (ремень)
        high_idx = np.searchsorted(freqs, 2000)
        high_energy = np.mean(amps[high_idx:])
        score_squeal = min(high_energy / (np.mean(amps) + 1e-9), 1.0)

        # 🔥 РЕШЕНИЕ

        if score_knock > 0.6:
            return {
                "type": "valve_clatter",
                "rpm": rpm,
                "confidence": round(score_knock, 2),
                "recommendation": "Обнаружен возможный стук гидрокомпенсаторов"
            }

        if score_squeal > 0.6:
            return {
                "type": "belt_squeal",
                "rpm": rpm,
                "confidence": round(score_squeal, 2),
                "recommendation": "Возможен свист ремня. Проверь натяжение."
            }

        return {
            "type": "normal_operation",
            "rpm": rpm,
            "confidence": 0.9,
            "recommendation": "Двигатель работает нормально"
        }


# 🔹 создаем анализатор
analyzer = EngineAnalyzer()


# 🔹 Главная страница
@app.route("/")
def home():
    return render_template("index.html")


# 🔹 API анализ
@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files["file"]

    try:
        with wave.open(file, 'rb') as wf:
            audio = np.frombuffer(
                wf.readframes(wf.getnframes()),
                dtype=np.int16
            ).astype(np.float32) / 32768.0

            # если стерео → делаем моно
            if wf.getnchannels() > 1:
                audio = audio.reshape(-1, wf.getnchannels()).mean(axis=1)

            sr = wf.getframerate()

        result = analyzer.process(audio, sr)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": "Ошибка чтения WAV файла"}), 500


# 🔹 запуск
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)