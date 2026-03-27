import os
import wave
import numpy as np
from flask import Flask, request, jsonify, render_template, send_from_directory
from pydub import AudioSegment
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
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(temp_path)

        wav_path = os.path.join(app.config['UPLOAD_FOLDER'], "temp_audio.wav")
        # Конвертируем звук в легкий формат
        audio_segment = AudioSegment.from_file(temp_path)
        audio_segment = audio_segment.set_channels(1).set_frame_rate(22050)
        audio_segment.export(wav_path, format="wav")

        # Читаем звук легким способом (чтобы сервер не упал в обморок)
        with wave.open(wav_path, 'rb') as wf:
            sr = wf.getframerate()
            audio_data = wf.readframes(wf.getnframes())
            audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

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