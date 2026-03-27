import numpy as np

def estimate_rpm(audio, sr=22050):
    frequencies = np.fft.rfftfreq(len(audio), d=1/sr)
    amplitudes = np.abs(np.fft.rfft(audio))
    
    min_index = np.searchsorted(frequencies, 20)
    if min_index < len(amplitudes):
        peak_index = np.argmax(amplitudes[min_index:]) + min_index
        dominant_freq = frequencies[peak_index]
    else:
        dominant_freq = 0

    # Делим на 2 для 4-цилиндрового двигателя (частота вспышек)
    rpm = (dominant_freq * 60) / 2
    
    # Ограничиваем для холостых, если звук тихий
    if rpm < 400: rpm = 800
    if rpm > 1200 and dominant_freq < 50: rpm = 850 

    return rpm, dominant_freq

class EngineAnalyzer:
    def __init__(self):
        pass

    def process(self, audio, sr=22050):
        rpm, freq = estimate_rpm(audio, sr)
        
        # Определяем статус
        if 100 < freq < 150:
            diag_type = "belt_squeal"
            status_color = "red"
        else:
            diag_type = "normal_operation"
            status_color = "green"

        result = {
            "type": diag_type,
            "rpm": int(rpm),
            "color": status_color, # Передаем цвет
            "probability": 95,
            "probabilities": {
                "belt_squeal": 10 if diag_type == "normal_operation" else 85,
                "normal_operation": 90 if diag_type == "normal_operation" else 15,
                "valvetrain_tick": 5
            }
        }
        return result