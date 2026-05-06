import numpy as np

SAMPLING_RATE = 250
WINDOW_TIME_FRAME = 5
SAMPLES_PER_WINDOW = SAMPLING_RATE * WINDOW_TIME_FRAME

FREQS = [7.5, 8.57, 10.0, 12.0, 15.0, 8.0] 
FREQ_COLORS = {
    6.66: "blue",
    7.50: "green",
    8.57: "orange",
    10.00: "red",
    12.00: "purple",
}

TARGET_CHANNELS = [1, 2, 3]

# Savitzky-Golay parameters
SG_WINDOW = 21
SG_POLYORDER = 3

# Faza offline (1000 = 1 sekunda)
TRIAL_DURATION_MS = 3000  # Czas patrzenia na kafelek
REST_DURATION_MS = 1000   # Czas przerwy na odpoczynek oczu