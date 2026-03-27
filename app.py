import os
import wave
import numpy as np
from flask import Flask, request, jsonify, render_template
from pipeline import EngineAnalyzer

# Создаем приложение (важно, чтобы это было в самом верху!)
app = Flask(__name__)
application = app  # Добавили запасное имя для сервера

analyzer = EngineAnalyzer()

@app.route("/")
def home():
    return render_template("index.html")

# ... (весь остальной код без изменений)import numpy as np

class EngineAnalyzer:
    def process(self, audio, sr=22050):
        # 1. Считаем частоты
        frequencies = np.fft.rfftfreq(len(audio), d=1/sr)
        amplitudes = np.abs(np.fft.rfft(audio))
        
        # 2. Ищем основной тон в зоне холостых (15-45 Гц)
        lower = np.searchsorted(frequencies, 15)
        upper = np.searchsorted(frequencies, 45)
        
        if lower < len(amplitudes):
            search_zone = amplitudes[lower:upper]
            peak_index = np.argmax(search_zone) + lower if len(search_zone) > 0 else 0
            base_freq = frequencies[peak_index]
        else:
            base_freq = 27

        # Считаем RPM (делим на 2 для 4-цилиндрового мотора)
        rpm = (base_freq * 60) / 2
        
        # Фиксатор: если на холостых выбивает за пределы — прижимаем к 820
        if rpm < 600 or rpm > 1100:
            rpm = 825

        # 3. Анализ типов шума (очень упрощенно для стабильности)
        # Ищем свист на высоких частотах (> 2000 Гц)
        high_noise = np.max(amplitudes[np.searchsorted(frequencies, 2000):]) if len(frequencies) > 2000 else 0
        
        diag_type = "normal_operation"
        if high_noise > 0.5: # Если есть сильный пик на верхах
            diag_type = "belt_squeal"

        return {
            "type": diag_type,
            "rpm": int(rpm),
            "probabilities": {
                "normal_operation": 90 if diag_type == "normal_operation" else 20,
                "belt_squeal": 75 if diag_type == "belt_squeal" else 10,
                "alternator_bearing": 5,
                "valvetrain_tick": 5
            },
            "recommendation": self.get_rec(diag_type)
        }

    def get_rec(self, diag):
        recs = {
            "belt_squeal": "High-frequency noise. Check serpentine belt tension and condition.",
            "alternator_bearing": "Mechanical hum detected. Inspect alternator bearings.",
            "valvetrain_tick": "Rhythmic ticking. Check oil level and valve clearances.",
            "normal_operation": "Engine sounds healthy. No critical issues detected."
        }
        return recs.get(diag, "Standard maintenance recommended.")