import os
import wave
import numpy as np
from flask import Flask, request, jsonify, render_template
from pipeline import EngineAnalyzer

app = Flask(__name__)
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
        # Читаем WAV напрямую
        with wave.open(file, 'rb') as wf:
            sr = wf.getframerate()
            n_channels = wf.getnchannels()
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            if n_channels > 1:
                audio = audio.reshape(-1, n_channels).mean(axis=1)

        result = analyzer.process(audio, sr)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}. Use only .WAV files!"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))