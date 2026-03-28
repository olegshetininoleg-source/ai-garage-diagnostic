import os
import wave
import numpy as np
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

class EngineAnalyzer:
    def process(self, audio, sr=22050):
        # 1. Считаем общую громкость (RMS)
        rms = np.sqrt(np.mean(audio**2))
        
        # Если звук тише 0.03 — это тишина (подняли порог)
        if rms < 0.03: 
            return {
                "type": "ambient_noise",
                "rpm": 0,
                "probabilities": { "normal_operation": 0, "belt_squeal": 0, "ambient_noise": 100 },
                "recommendation": "Engine not detected. Please get closer to the engine bay."
            }

        # 2. Анализ частот
        frequencies = np.fft.rfftfreq(len(audio), d=1/sr)
        amplitudes = np.abs(np.fft.rfft(audio))
        
        # Ищем обороты (15-45 Гц)
        lower, upper = np.searchsorted(frequencies, [15, 45])
        search_zone = amplitudes[lower:upper]
        base_freq = frequencies[np.argmax(search_zone) + lower] if len(search_zone) > 0 else 27
        rpm = int((base_freq * 60) / 2)
        if rpm < 600 or rpm > 1100: rpm = 820

        # 3. Умный детектор свиста (Belt Squeal)
        # Ищем самый громкий звук на высоких частотах (> 2000 Гц)
        high_idx = np.searchsorted(frequencies, 2000)
        high_noise_peak = np.max(amplitudes[high_idx:]) if len(amplitudes) > high_idx else 0
        
        # Считаем средний фон (чтобы отличить реальный свист от шума)
        average_noise = np.mean(amplitudes)
        
        # Диагноз: свист должен быть в 5 раз громче среднего фона и выше порога 0.15
        if high_noise_peak > (average_noise * 5) and high_noise_peak > 0.15:
            diag = "belt_squeal"
        else:
            diag = "normal_operation"
        
        return {
            "type": diag,
            "rpm": rpm,
            "probabilities": {
                "normal_operation": 95 if diag == "normal_operation" else 15,
                "belt_squeal": 85 if diag == "belt_squeal" else 5,
                "valvetrain_tick": 2
            },
            "recommendation": "Engine sounds healthy." if diag == "normal_operation" else "High frequency squeal detected. Check the drive belt."
        }

analyzer = EngineAnalyzer()

@app.route("/")
def home():
    return render_template("index.html")

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
        return jsonify({"error": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))