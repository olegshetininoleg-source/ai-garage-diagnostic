import librosa
from pipeline import EngineAnalyzer

def main():
    # ⚠️ сюда положи аудиофайл двигателя
    audio, sr = librosa.load("engine.wav", sr=22050)

    analyzer = EngineAnalyzer(sr)
    result = analyzer.process(audio)

    print("\nRESULT:")
    print(result)


if __name__ == "__main__":
    main()