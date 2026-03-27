import os
import wave
import numpy as np
from flask import Flask, request, jsonify, render_template, send_from_directory
from pipeline import EngineAnalyzer
from pdf_maker import generate_report

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

analyzer = EngineAnalyzer()

@app.route("/")
def home(): return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    try:
        wav_path = os.path.join(app.config['UPLOAD_FOLDER'], "temp.wav")
        file.save(wav_path)
        with wave.open(wav_path, 'rb') as wf:
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            if wf.getnchannels() > 1: audio = audio.reshape(-1, wf.getnchannels()).mean(axis=1)
            sr = wf.getframerate()

        result = analyzer.process(audio, sr)
        
        # Генерация PDF с учетом рекомендации
        pdf_name = f"Report_{int(result['rpm'])}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
        generate_report(result['rpm'], result['type'], result['probabilities'], result['recommendation'], pdf_path)
        
        result['pdf_url'] = f"/download/{pdf_name}"
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))