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
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        # Сохраняем файл (поддерживаем только .wav для легкости)
        wav_path = os.path.join(app.config['UPLOAD_FOLDER'], "temp_audio.wav")
        file.save(wav_path)

        # Читаем звук максимально легким способом
        with wave.open(wav_path, 'rb') as wf:
            n_channels = wf.getnchannels()
            sr = wf.getframerate()
            frames = wf.readframes(wf.getnframes())
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            # Если стерео — делаем моно
            if n_channels > 1:
                audio = audio.reshape(-1, n_channels).mean(axis=1)

        result = analyzer.process(audio, sr)
        
        pdf_name = f"Report_{int(result['rpm'])}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
        generate_report(result['rpm'], result['type'], result['probabilities'], pdf_path)
        
        result['pdf_url'] = f"/download/{pdf_name}"
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)