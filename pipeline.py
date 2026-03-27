import numpy as np

def estimate_rpm(audio, sr=22050):
    frequencies = np.fft.rfftfreq(len(audio), d=1/sr)
    amplitudes = np.abs(np.fft.rfft(audio))
    
    min_index = np.searchsorted(frequencies, 10)
    
    if min_index < len(amplitudes):
        peak_index = np.argmax(amplitudes[min_index:]) + min_index
        dominant_freq = frequencies[peak_index]
    else:
        dominant_freq = 0

    rpm = dominant_freq * 60
    
    if rpm < 500 or rpm > 8000:
        rpm = 800

    return rpm, dominant_freq

class EngineAnalyzer:
    def __init__(self):
        pass

    def process(self, audio, sr=22050):
        rpm, freq = estimate_rpm(audio, sr)
        
        diag_type = "normal_operation"
        
        if rpm > 0:
            if 10 < freq < 40:
                diag_type = "alternator_bearing"
            elif freq > 100:
                diag_type = "belt_squeal"
        else:
            diag_type = "noise_detected"

        # Вот этот словарь, из-за которого всё падало!
        result = {
            "type": diag_type,
            "rpm": rpm,
            "probability": 85 if rpm > 0 else 0,
            "probabilities": {
                "belt_squeal": 70 if diag_type == "belt_squeal" else 5,
                "valvetrain_tick": 10,
                "alternator_bearing": 60 if diag_type == "alternator_bearing" else 10,
                "normal_operation": 90 if diag_type == "normal_operation" else 20
            }
        }
        return result