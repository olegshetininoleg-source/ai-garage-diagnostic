def classify_anomaly(freq, kurt, rpm, flux, features):
    centroid = features["centroid_mean"]
    rms_std = features["rms_std"]
    zcr = features["zcr_mean"]

    if kurt < 3.5 and flux < 2 and rms_std < 0.01:
        return "normal_operation"

    if 800 < freq < 2000 and 4 < kurt < 6 and centroid > 1000:
        return "valve_clatter"

    if kurt > 6 and flux > 5 and rms_std > 0.02:
        return "rod_knock"

    if centroid > 3000 and zcr > 0.1:
        return "belt_whistle"

    if freq < 300 and rms_std < 0.02:
        return "bearing_noise"

    return "unknown"