import numpy as np
from scipy.stats import kurtosis

def compute_kurtosis(audio):
    return float(kurtosis(audio, fisher=False))

def detect_anomalies(S_db, threshold=15):
    anomalies = []

    for t in range(S_db.shape[1]):
        frame = S_db[:, t]
        if np.max(frame) - np.mean(frame) > threshold:
            anomalies.append(t)

    return anomalies

def spectral_flux(S_db):
    return np.sqrt(np.sum(np.diff(S_db, axis=1) ** 2, axis=0))