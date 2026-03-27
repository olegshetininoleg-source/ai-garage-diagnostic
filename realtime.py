import numpy as np
import sounddevice as sd
from collections import deque

from pipeline import EngineAnalyzer


sr = 22050
buffer = deque(maxlen=sr * 3)  # 3 секунды

analyzer = EngineAnalyzer(sr)


def callback(indata, frames, time, status):
    if status:
        print(status)

    audio = indata[:, 0]
    buffer.extend(audio)


def main():
    print("🎤 Слушаю двигатель... (Ctrl+C чтобы остановить)")

    with sd.InputStream(samplerate=sr, channels=1, callback=callback):
        while True:
            if len(buffer) < sr * 2:
                continue

            audio = np.array(buffer)

            result = analyzer.process(audio)

            print(result)


if __name__ == "__main__":
    main()