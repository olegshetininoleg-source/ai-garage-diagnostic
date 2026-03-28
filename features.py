import numpy as np
import librosa

def extract_advanced_features(audio, sr):
    features = {}

    rms = librosa.feature.rms(y=audio)[0]
    features["rms_mean"] = float(np.mean(rms))
    features["rms_std"] = float(np.std(rms))

    centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
    features["centroid_mean"] = float(np.mean(centroid))

    zcr = librosa.feature.zero_crossing_rate(audio)[0]
    features["zcr_mean"] = float(np.mean(zcr))

    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
    features["mfcc_mean"] = mfcc.mean(axis=1).tolist()

    S = np.abs(librosa.stft(audio))
    flux = np.sqrt(np.sum(np.diff(S, axis=1)**2, axis=0))
    features["flux_mean"] = float(np.mean(flux))
    features["flux_std"] = float(np.std(flux))

    return features