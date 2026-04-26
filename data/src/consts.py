import numpy as np

SAMPLING_RATE = 250
WINDOW_TIME_FRAME = 5
SAMPLES_PER_WINDOW = SAMPLING_RATE * WINDOW_TIME_FRAME

EXPECTED_FREQS = [6.66, 7.50, 8.57, 10.00, 12.00]
FREQ_COLORS = {
    6.66: "blue",
    7.50: "green",
    8.57: "orange",
    10.00: "red",
    12.00: "purple",
}

TARGET_CHANNELS = []

# Savitzky-Golay parameters
SG_WINDOW = 21
SG_POLYORDER = 3
