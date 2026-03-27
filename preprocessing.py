import numpy as np
import scipy.signal as signal

def highpass_filter(audio, sr, cutoff=90.0, order=4):
    nyquist = 0.5 * sr
    norm_cutoff = cutoff / nyquist
    b, a = signal.butter(order, norm_cutoff, btype='high')
    return signal.filtfilt(b, a, audio)