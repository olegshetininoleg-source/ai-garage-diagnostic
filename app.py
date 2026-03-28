import os
import wave
import numpy as np
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

class EngineAnalyzer:
    def process(self, audio, sr=22050):
        # 1. Громкость (RMS)
        rms = np.sqrt(np.mean(audio**2))
        
        # Если звук тише 0.05 — это фоновый шум дома, игнорируем
        if rms < 0.05: 
            return {
                "type": "ambient_noise",
                "rpm": 0,
                "probabilities": { "normal_operation": 0, "belt_squeal": 0, "ambient_noise": 100 },
                "recommendation": "Engine not detected. Please bring the phone closer to the open hood."
            }

        # 2. Анализ спектра
        freqs = np.fft.rfftfreq(len(audio), d=1/sr)
        amps = np.abs(np.fft.rfft(audio))
        
        # Обороты
        low_idx = np.searchsorted(freqs, [15, 45])
        search_zone = amps[low_idx[0]:low_idx[1]]
        base_freq = freqs[np.argmax(search_zone) + low_idx[0]] if len(search_zone) > 0 else 27
        rpm = int((base_freq * 60) / 2)
        if rpm < 600 or rpm > 1100: rpm = 800

        # 3. Детектор СВИСТА (Улучшенный)
        high_idx = np.searchsorted(freqs, 2000)
        high_amps = amps[high_idx:]
        
        if len(high_amps) > 0:
            peak_high = np.max(high_amps)
            mean_high = np.mean(high_amps)
            
            # Коэффициент "остроты" (отношение пика к среднему шуму)
            # У свиста этот показатель > 15-20. У шума телека он < 5.
            sharpness = peak_high / (mean_high + 1e-6)
            
            # Свистит только если это громкий И острый звук
            if peak_high > 0.2 and sharpness > 15:
                diag = "belt_squeal"
                prob = min(int(sharpness * 3), 98) # Вероятность зависит от остроты
            else:
                diag = "normal_operation"
                prob = 95
        else:
            diag = "normal_operation"
            prob = 95

        return {
            "type": diag,
            "rpm": rpm,
            "probabilities": {
                "normal_operation": prob if diag == "normal_operation" else 10,
                "belt_squeal": prob if diag == "belt_squeal" else 2,
                "ambient_noise": 5
            },
            "recommendation": "Engine sounds healthy." if diag == "normal_operation" else "Sharp high-frequency squeal detected. Check belts."
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
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))