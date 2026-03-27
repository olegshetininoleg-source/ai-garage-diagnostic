import numpy as np

class TemporalAnalyzer:
    def __init__(self, window_size=20):
        self.history = []
        self.window_size = window_size

    def update(self, value):
        self.history.append(value)
        if len(self.history) > self.window_size:
            self.history.pop(0)

    def is_unstable(self, threshold=5.0):
        if len(self.history) < 2:
            return False
        return np.var(self.history) > threshold