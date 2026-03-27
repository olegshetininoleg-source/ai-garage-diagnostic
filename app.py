import os
from flask import Flask, request, jsonify, render_template, send_from_directory
import librosa
from pydub import AudioSegment
from pipeline import EngineAnalyzer
from pdf_maker import generate_report

app = Flask(__name__)

# Папка для временных файлов (создастся сама)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
        # 1. Сохраняем файл на диск, чтобы pydub мог его обработать
        ext = os.path.splitext(file.filename)[1].lower()
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(temp_path)

        # 2. Конвертируем в WAV, если это M4A, MP3 или AAC
        wav_path = os.path.join(app.config['UPLOAD_FOLDER'], "temp_audio.wav")
        audio_converted = AudioSegment.from_file(temp_path)
        audio_converted.export(wav_path, format="wav")

        # 3. Загружаем обработанный WAV в либрозу
        audio, sr = librosa.load(wav_path, sr=22050)
        
        # 4. Анализ
        result = analyzer.process(audio)
        
        # 5. Генерируем PDF (берем данные из результата анализа)
        # result['type'] - название поломки, result['rpm'] - обороты
        pdf_name = f"Report_{int(result['rpm'])}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
        
        # Передаем данные в наш генератор PDF
        generate_report(result['rpm'], result['type'], result['probabilities'], pdf_path)
        
        # Добавляем ссылку на PDF в ответ, чтобы фронтенд мог её показать
        result['pdf_url'] = f"/download/{pdf_name}"
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

# Маршрут для скачивания готового PDF
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    import os
<<<<<<< HEAD
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
=======
    # Берем порт, который дает нам облачный сервис (по умолчанию 5000)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
>>>>>>> b8c4ec49886f9c47b49c0ebef0736bbd8cda6454
