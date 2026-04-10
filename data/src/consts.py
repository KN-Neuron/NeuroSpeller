import numpy as np

SAMPLING_RATE = 250
WINDOW_TIME_FRAME = 5
SAMPLES_PER_5_SEC = SAMPLING_RATE * WINDOW_TIME_FRAME
ADAPT_TRIALS = 8

EXPECTED_FREQS = [6.66, 7.50, 8.57, 10.00, 12.00]
FREQ_COLORS = {
    6.66: "blue",
    7.50: "green",
    8.57: "orange",
    10.00: "red",
    12.00: "purple",
}

# Savitzky-Golay parameters
SG_WINDOW = 21
SG_POLYORDER = 3

# SNR parameters
SNR_NEIGHBOR_BINS = 5
SNR_EXCLUDE_BINS = 2
SNR_THRESHOLD_LINEAR = 3.0
SNR_THRESHOLD_DB = 10 * np.log10(SNR_THRESHOLD_LINEAR)
CONFIDENCE_LEVEL = 0.80

# labels in the .mat files
EEG_KEY = "eeg"
DIN_KEY = "DIN_1"

# Channels of interest (occipital)
CHANNELS = {
    125: "Oz",
    115: "O1",
    149: "O2",
}

# Extended channels for time-domain plots
CHANNELS_TIME = {125: "Oz", 115: "O1", 149: "O2", 101: "Pz"}

OUTPUT_DIR = "ssvep_analysis_output"
