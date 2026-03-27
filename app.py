import os
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
def home(): return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files: return jsonify({"error": "No file"}), 400
    file = request.files["file"]
    
    try:
        # 1. Сохраняем временный файл
        ext = os.path.splitext(file.filename)[1].lower()
        raw_path = os.path.join(app.config['UPLOAD_FOLDER'], f"raw_audio{ext}")
        file.save(raw_path)

        # 2. Конвертируем в WAV (теперь это сработает!)
        audio_segment = AudioSegment.from_file(raw_path)
        audio_segment = audio_segment.set_channels(1).set_frame_rate(22050)
        
        # Переводим в массив numpy для анализа
        samples = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
        # Нормализация громкости
        if audio_segment.sample_width == 2:
            samples /= 32768.0
        elif audio_segment.sample_width == 4:
            samples /= 2147483648.0

        # 3. Анализируем
        result = analyzer.process(samples, 22050)
        
        # 4. Генерируем PDF
        pdf_name = f"Report_{int(result['rpm'])}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
        generate_report(result['rpm'], result['type'], result['probabilities'], result['recommendation'], pdf_path)
        
        result['pdf_url'] = f"/download/{pdf_name}"
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Format error: {str(e)}. Try uploading a WAV or MP3."}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))