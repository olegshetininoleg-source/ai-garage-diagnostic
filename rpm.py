import numpy as np
import scipy.signal as signal

def estimate_rpm(audio, sr, cylinders=4):
    # 1. Убираем смещение
    audio = audio - np.mean(audio)

    # 2. Фильтруем высокие шумы (свист ремней, ветер)
    nyquist = 0.5 * sr
    b, a = signal.butter(4, [10.0 / nyquist, 200.0 / nyquist], btype='band')
    filtered_audio = signal.filtfilt(b, a, audio)

    # 3. ПЕРЕХОДИМ НА ФУРЬЕ (Метод Уэлча)
    # Этот метод найдет самую мощную частоту баса, игнорируя шумы.
    # Разрешение спектра ~0.5 Гц для высокой точности
    nperseg = min(len(filtered_audio), sr * 2) 
    if nperseg == 0:
        return 0, 0.0
        
    freqs, psd = signal.welch(filtered_audio, sr, nperseg=nperseg)

    # 4. Задаем физические рамки для 4-тактного двигателя
    # Частота вспышек (Гц) = (RPM / 60) * (cylinders / 2)
    # Для 4 цилиндров: RPM = Freq * 30
    min_freq = 400.0 / 30.0   # ~13.3 Гц (400 об/мин)
    max_freq = 6000.0 / 30.0  # 200.0 Гц (6000 об/мин)

    # Отрезаем всё, что выходит за эти рамки
    valid_idx = np.where((freqs >= min_freq) & (freqs <= max_freq))[0]
    
    if len(valid_idx) == 0:
        return 0, 0.0

    valid_freqs = freqs[valid_idx]
    valid_psd = psd[valid_idx]

    # 5. Ищем частоту с максимальной энергией
    best_freq = valid_freqs[np.argmax(valid_psd)]

    # 6. Переводим частоту обратно в обороты
    rpm = best_freq * 120 / cylinders

    return int(rpm), float(best_freq)