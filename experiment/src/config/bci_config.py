import numpy as np

SAMPLING_RATE = 250
WINDOW_TIME_FRAME = 5
SAMPLES_PER_WINDOW = SAMPLING_RATE * WINDOW_TIME_FRAME

FREQS = [6, 7.5, 8.57, 10, 12, 15]

TARGET_CHANNELS = [11, 6, 1]

# Savitzky-Golay parameters
SG_WINDOW = 21
SG_POLYORDER = 3

# Faza offline (1000 = 1 sekunda)
TRIAL_DURATION_MS = 5000  # Czas patrzenia na kafelek
REST_DURATION_MS = 1000   # Czas przerwy na odpoczynek oczu