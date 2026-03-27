import numpy as np

from preprocessing import highpass_filter
from features import compute_spectrogram, extract_advanced_features
from rpm import estimate_rpm
from anomaly import detect_anomalies, compute_kurtosis, spectral_flux
from classifier import classify_anomaly
from temporal_analysis import TemporalAnalyzer


class EngineAnalyzer:
    def __init__(self, sr=22050, cylinders=4):
        self.sr = sr
        self.cylinders = cylinders
        self.temporal = TemporalAnalyzer()

    def process(self, audio):
        # 1. Очистка звука
        audio = highpass_filter(audio, self.sr)

        # 2. Получение спектрограммы
        S_db = compute_spectrogram(audio, self.sr)

        # 3. Расчет оборотов (RPM)
        rpm, freq = estimate_rpm(audio, self.sr, self.cylinders)

        # 4. Поиск аномалий и базовые расчеты
        anomalies = detect_anomalies(S_db)
        kurt = compute_kurtosis(audio)

        flux = np.mean(spectral_flux(S_db))

        # 5. Извлечение продвинутых признаков
        features = extract_advanced_features(audio, self.sr)

        # 6. Временной анализ
        self.temporal.update(flux)
        unstable = self.temporal.is_unstable()

        # 7. Классификация главной проблемы
        anomaly_type = classify_anomaly(freq, kurt, rpm, flux, features)

        # 8. Расчет уверенности (confidence)
        confidence = self.compute_confidence(
            anomaly_type, kurt, flux, features, anomalies
        )

        # 9. Генерируем массив вероятностей для графиков на сайте
        probs = self.generate_probabilities(anomaly_type, confidence)

        # ВОЗВРАЩАЕМ ПОЛНЫЙ СЛОВАРЬ (включая probabilities!)
        return {
            "anomaly_detected": anomaly_type != "normal_operation",
            "type": anomaly_type,
            "confidence": round(confidence, 2),
            "rpm": int(rpm),
            "freq": float(freq),
            "centroid": features["centroid_mean"],
            "probabilities": probs  # <-- ТА САМАЯ СТРОЧКА
        }

    def compute_confidence(self, anomaly_type, kurt, flux, features, anomalies):
        score = 0.0

        score += min(kurt / 10, 0.3)
        score += min(flux / 10, 0.3)
        score += min(features["rms_std"] * 10, 0.2)
        score += min(len(anomalies) / 50, 0.2)

        if anomaly_type == "normal_operation":
            return max(0.1, 1.0 - score)

        return min(1.0, score)

    def generate_probabilities(self, main_type, main_confidence):
        main_pct = int(main_confidence * 100)
        
        probs = {
            "valvetrain_tick": 3,
            "alternator_bearing": 2,
            "belt_squeal": 2,
            "engine_knock": 1,
            "normal_operation": 5
        }

        probs[main_type] = main_pct

        remaining = max(0, 100 - main_pct)
        if remaining > 0:
            # Исправленная строка со скобкой
            keys = [k for k in probs.keys() if k != main_type]
            probs[keys[0]] += int(remaining * 0.7)
            probs[keys[1]] += int(remaining * 0.3)

        return dict(sorted(probs.items(), key=lambda item: item[1], reverse=True))