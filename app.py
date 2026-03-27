from flask import Flask, request, jsonify, render_template
import librosa
import numpy as np
from pipeline import EngineAnalyzer

app = Flask(__name__)
# Запускаем твой анализатор
analyzer = EngineAnalyzer()

# 1. Загрузка главной страницы (интерфейса)
@app.route("/")
def home():
    return render_template("index.html")

# 2. Прием и обработка файла от пользователя
@app.route("/analyze", methods=["POST"])
def analyze():
    # Проверка 1: Есть ли вообще файл в запросе?
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    
    # Проверка 2: Выбрал ли пользователь файл перед отправкой?
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        # Читаем аудио напрямую из оперативной памяти (без сохранения на жесткий диск)
        audio, sr = librosa.load(file, sr=22050)
        
        # Пропускаем звук через твою нейросеть
        result = analyzer.process(audio)
        
        # Возвращаем результат обратно в index.html
        return jsonify(result)
        
    except Exception as e:
        # Если загрузили не аудио или произошла ошибка
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

# Запуск сервера
if __name__ == "__main__":
    app.run(debug=True)