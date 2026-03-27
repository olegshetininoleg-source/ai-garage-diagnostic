import numpy as np
import librosa


def compute_spectrogram(audio, sr):
    S = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128)
    return librosa.power_to_db(S, ref=np.max)


def extract_advanced_features(audio, sr):
    features = {}

    rms = librosa.feature.rms(y=audio)[0]
    features["rms_mean"] = float(np.mean(rms))
    features["rms_std"] = float(np.std(rms))

    centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
    features["centroid_mean"] = float(np.mean(centroid))

    zcr = librosa.feature.zero_crossing_rate(audio)[0]
    features["zcr_mean"] = float(np.mean(zcr))

    return features