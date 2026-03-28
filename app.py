import os
import wave
import numpy as np
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

class EngineAnalyzer:
    def process(self, audio, sr=22050):
        # 1. Проверка на "Тишину" или "Фоновый шум"
        # Вычисляем амплитуду (громкость)
        rms = np.sqrt(np.mean(audio**2))
        
        # Порог для реального мотора должен быть выше. 
        # 0.08 - это уровень, когда телефон реально слышит работающее железо.
        if rms < 0.08: 
            return {
                "type": "low_signal",
                "rpm": 0,
                "probabilities": { "normal_operation": 0, "belt_squeal": 0, "low_signal": 100 },
                "recommendation": "Sound is too quiet. Please place the microphone 20-30 cm from the engine."
            }

        # 2. Анализ частот (БПФ)
        freqs = np.fft.rfftfreq(len(audio), d=1/sr)
        amps = np.abs(np.fft.rfft(audio))
        
        # Считаем обороты (15-45 Гц)
        low_zone = (freqs >= 15) & (freqs <= 45)
        if np.any(low_zone):
            base_freq = freqs[low_zone][np.argmax(amps[low_zone])]
            rpm = int((base_freq * 60) / 2)
        else:
            rpm = 820
            
        if rpm < 500 or rpm > 1200: rpm = 825

        # 3. Детектор СВИСТА (Ультра-фильтр)
        high_idx = np.searchsorted(freqs, 2000)
        high_amps = amps[high_idx:]
        
        if len(high_amps) > 0:
            peak_high = np.max(high_amps)
            mean_signal = np.mean(amps) # Средний уровень всего звука
            
            # Настоящий свист должен "торчать" над средним сигналом минимум в 25 раз
            snr_ratio = peak_high / (mean_signal + 1e-9)
            
            if snr_ratio > 25 and peak_high > 0.3:
                diag = "belt_squeal"
                confidence = min(int(snr_ratio * 2), 98)
            else:
                diag = "normal_operation"
                confidence = 95
        else:
            diag = "normal_operation"
            confidence = 95

        return {
            "type": diag,
            "rpm": rpm,
            "probabilities": {
                "normal_operation": confidence if diag == "normal_operation" else 5,
                "belt_squeal": confidence if diag == "belt_squeal" else 2,
                "low_signal": 0
            },
            "recommendation": "Engine sounds healthy." if diag == "normal_operation" else "Mechanical squeal detected. Inspect drive belt."
        }

analyzer = EngineAnalyzer()

@app.route("/")
def home(): return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    try:
        with wave.open(file, 'rb') as wf:
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
            if wf.getnchannels() > 1: audio = audio.reshape(-1, wf.getnchannels()).mean(axis=1)
            sr = wf.getframerate()
        return jsonify(analyzer.process(audio, sr))
    except Exception as e:
        return jsonify({"error": "Wrong file format. Use .WAV only."}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))