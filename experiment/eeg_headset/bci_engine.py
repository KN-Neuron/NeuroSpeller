import numpy as np
from scipy.signal import savgol_filter
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
data_src_path = os.path.abspath(os.path.join(current_dir, '..', '..', 'data', 'src'))

if data_src_path not in sys.path:
    sys.path.append(data_src_path)

from data.src.fft_analysis import compute_fft_magnitude
from data.src.consts import EXPECTED_FREQS, SG_WINDOW, SG_POLYORDER


class BCIEngine:
    def __init__(self, streamer, threshold=1.5):
        self.streamer = streamer
        self.threshold = threshold
        # Które kanały, trzeba zobaczyć w dokumentacji czepka
        self.target_channels = [1, 6, 11]

    def predict(self):
        epoch = self.streamer.get_current_window()

        if np.all(epoch == 0):
            return None

        # PREPROCESSING: CAR Common Average Reference
        # Od każdego kanału odejmujemy średnią ze wszystkich kanałów w danej chwili
        # To usuwa szum wspólny dla całej głowy
        mean_signal = np.mean(epoch, axis=0)
        car_epoch = epoch - mean_signal

        # ANALIZA WIELOKANAŁOWA
        # Będziemy zbierać wyniki mocy z każdego interesującego nas kanału
        channel_results = []

        for ch_idx in self.target_channels:
            raw_signal = car_epoch[ch_idx, :]

            # Filtrowanie (Savgol)
            filtered_signal = savgol_filter(raw_signal, SG_WINDOW, SG_POLYORDER)

            # Liczymy FFT
            magnitude = compute_fft_magnitude(filtered_signal)
            channel_results.append(magnitude)

        # Uśredniamy widmo (magnitude) ze wszystkich wybranych kanałów
        # Dzięki temu "wzmacniamy" to, co widzą wszystkie elektrody na raz
        avg_magnitude = np.mean(channel_results, axis=0)

        max_samples = epoch.shape[1]
        freqs_fft = np.fft.rfftfreq(max_samples, d=1.0 / self.streamer.sampling_rate)

        best_freq = None
        max_mag = 0

        for expected_freq in EXPECTED_FREQS:
            target_bin = np.argmin(np.abs(freqs_fft - expected_freq))
            peak_value = avg_magnitude[target_bin]

            if peak_value > max_mag:
                max_mag = peak_value
                best_freq = expected_freq

        if max_mag > self.threshold:
            return best_freq

        return None