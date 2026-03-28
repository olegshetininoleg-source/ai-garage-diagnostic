import os
import wave
import numpy as np
from flask import Flask, request, jsonify, render_template
from scipy.signal import butter, filtfilt, hilbert
from scipy.stats import kurtosis

app = Flask(__name__)

class EngineAnalyzer:
    # Опускаем с 300 Гц до 100 Гц, чтобы не отрезать звук самого мотора!
    def bandpass_filter(self, audio, sr, low=100, high=4000):
        nyq = 0.5 * sr
        b, a = butter(4, [low / nyq, high / nyq], btype='band')
        return filtfilt(b, a, audio)

    # Огибающая для поиска ритмичных ударов (стука)
    def compute_envelope(self, audio):
        analytic = hilbert(audio)
        return np.abs(analytic)

    def process(self, audio, sr=22050):
        # 1. Проверка громкости
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < 0.03: # Настроили чувствительность
            return {
                "type": "low_signal",
                "rpm": 0,
                "probabilities": { "normal_operation": 0, "belt_squeal": 0, "valve_clatter": 0 },
                "recommendation": "Запись слишком тихая. Поднесите телефон ближе к двигателю."
            }

        # 2. Фильтрация
        filtered = self.bandpass_filter(audio, sr)

        # 3. Kurtosis (индикатор резкого металлического стука)
        k = kurtosis(filtered)

        # 4. Поиск пиков (ударов клапанов/гидриков)
        env = self.compute_envelope(filtered)
        peak_count = np.sum(env > (np.mean(env) + 2 * np.std(env)))

        # 5. Анализ частот (БПФ)
        freqs = np.fft.rfftfreq(len(audio), d=1 / sr)
        amps = np.abs(np.fft.rfft(audio))

        # Обороты
        low_zone = (freqs >= 15) & (freqs <= 50)
        if np.any(low_zone):
            base_freq = freqs[low_zone][np.argmax(amps[low_zone])]
            rpm = int((base_freq * 60) / 2)
        else:
            rpm = 800
        if rpm < 500 or rpm > 1200: rpm = 825

        # 🔥 СКОРИНГ ВЕРОЯТНОСТЕЙ (для красивых шкал на сайте)

        # --- Стук (Valve Clatter)
        score_knock = min(max(k, 0) / 5, 0.5) 
        score_knock += min(peak_count / 1000, 0.5)
        prob_knock = int(score_knock * 100)

        # --- Свист (Belt Squeal)
        high_idx = np.searchsorted(freqs, 2000)
        high_energy = np.max(amps[high_idx:]) if len(amps[high_idx:]) > 0 else 0
        snr_ratio = high_energy / (np.mean(amps) + 1e-9)
        
        prob_squeal = 0
        if snr_ratio > 15 and high_energy > 0.2:
            prob_squeal = min(int((snr_ratio / 40) * 100), 95)

        # --- Норма
        prob_normal = max(100 - prob_knock - prob_squeal, 5)

        # 🔥 РЕШЕНИЕ
        diag_type = "normal_operation"
        rec = "Двигатель работает нормально. Критических шумов нет."

        if prob_knock > 45 and prob_knock > prob_squeal:
            diag_type = "valve_clatter"
            rec = "Обнаружен металлический стук (возможно, гидрокомпенсаторы или клапана)."
        elif prob_squeal > 45:
            diag_type = "belt_squeal"
            rec = "Обнаружен высокочастотный свист. Проверьте натяжение ремня генератора."

        return {
            "type": diag_type,
            "rpm": rpm,
            "probabilities": {
                "normal_operation": prob_normal,
                "belt_squeal": prob_squeal,
                "valve_clatter": prob_knock
            },
            "recommendation": rec
        }

analyzer = EngineAnalyzer()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    try:
        with wave.open(file, 'rb') as wf:
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
            if wf.getnchannels() > 1:
                audio = audio.reshape(-1, wf.getnchannels()).mean(axis=1)
            sr = wf.getframerate()
        return jsonify(analyzer.process(audio, sr))
    except Exception as e:
        return jsonify({"error": f"Ошибка чтения файла: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))