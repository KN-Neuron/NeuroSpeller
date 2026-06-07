import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from experiment.src.pipeline.predictor import CCAPredictor

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter, welch
from sklearn.cross_decomposition import CCA
from loader import load_data
from plots import plot_time_series, plot_fft, plot_psd

from experiment.src.config.bci_config import (
    SAMPLING_RATE,
    TARGET_CHANNELS,
    SG_WINDOW,
    SG_POLYORDER,
    FREQS,
    WINDOW_TIME_FRAME,
)
from experiment.src.pipeline.predictor import CCAPredictor

def main():
    filenames = [
        "kacper/kacper1.fif",
        "kacper/kacper2.fif",
        "kacper/kacper3.fif",
    ]

    for filename in filenames:
        print(f"\n{'='*50}\nPrzetwarzanie pliku: {filename}\n{'='*50}")
        data_dict = load_data(filename, target_marker_freqs=FREQS, l_freq=5.0, h_freq=45.0)

        if data_dict is not None:
            # Iteracja po słowniku z wyizolowanymi epokami dla każdej częstotliwości
            for target_freq, epoch_data in data_dict.items():
                print(
                    f"\n--- Analiza dla częstotliwości docelowej: {target_freq} Hz ---"
                )

                # Zabezpieczenie na wypadek, gdyby epoki nie pobrano prawidłowo
                if epoch_data.ndim < 2:
                    print(f"Pominięto {target_freq} Hz (brak danych).")
                    continue

                num_samples = epoch_data.shape[1]
                time = np.linspace(0, WINDOW_TIME_FRAME, num_samples, endpoint=False)

                # Operacja CAR (Common Average Reference) dla całej wyizolowanej epoki
                mean_signal = np.mean(epoch_data[TARGET_CHANNELS, :], axis=0)
                car_all_channels = epoch_data - mean_signal

                # Analiza per kanał (Time Series, FFT, PSD)
                for ch_idx in TARGET_CHANNELS:
                    print(f"  -> Rysowanie wykresów dla kanału nr {ch_idx}")

                    raw_signal = epoch_data[ch_idx, :]
                    car_signal = car_all_channels[ch_idx, :]
                    filtered_signal = savgol_filter(
                        car_signal, window_length=SG_WINDOW, polyorder=SG_POLYORDER
                    )

                    # 1. Wykres w dziedzinie czasu
                    plot_time_series(
                        time, raw_signal, car_signal, filtered_signal, ch_idx
                    )
                    filepath = os.path.join(
                        "plots",
                        "time_series",
                        filename,
                        str(ch_idx),
                        f"{target_freq}.png",
                    )
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    plt.savefig(filepath)
                    plt.close()

                    # 2. Wykres FFT (ponieważ plot_fft rysuje jedną linię, grupujemy je w jednej figurze)
                    plt.figure(figsize=(12, 6))
                    plot_fft(raw_signal, "Przed filtrem", "gray")
                    plot_fft(car_signal, "Po CAR", "blue")
                    plot_fft(filtered_signal, "Po filtrze Savitzky-Golay", "red")
                    plt.title(
                        f"Analiza częstotliwości FFT - Kanał {ch_idx} (Bodziec: {target_freq} Hz)"
                    )
                    filepath = os.path.join(
                        "plots", "fft", filename, str(ch_idx), f"{target_freq}.png"
                    )
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    plt.savefig(filepath)
                    plt.close()

                    # 3. Wykres PSD (Welch)
                    nperseg = min(2 * SAMPLING_RATE, len(raw_signal))
                    f_raw, psd_raw = welch(
                        raw_signal, fs=SAMPLING_RATE, nperseg=nperseg
                    )
                    f_filt, psd_filt = welch(
                        filtered_signal, fs=SAMPLING_RATE, nperseg=nperseg
                    )
                    plot_psd(f_raw, psd_raw, f_filt, psd_filt)
                    filepath = os.path.join(
                        "plots", "psd", filename, str(ch_idx), f"{target_freq}.png"
                    )
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    plt.savefig(filepath)
                    plt.close()

                # 4. CCA dla całej epoki (wykorzystuje zbiór kanałów docelowych)
                print("  -> Generowanie klasyfikacji CCA")
                epoch_X = car_all_channels[TARGET_CHANNELS, :].T

                predictor = CCAPredictor(
                    expected_frequencies=FREQS,
                    sampling_rate=SAMPLING_RATE,
                    window_length=num_samples,
                    threshold=0.5,
                )
                predicted_freq = predictor.predict(epoch_X)
                print(f"     Predykcja CCA: {predicted_freq} Hz (dla {target_freq} Hz)")
                print(
                    f"     Współczynniki korelacji CCA: {predictor.last_correlations}"
                )
                freqs_list = list(predictor.last_correlations.keys())
                corr_values = list(predictor.last_correlations.values())

                plt.figure(figsize=(10, 5))
                bars = plt.bar(
                    [str(f) for f in freqs_list], corr_values, color="teal", alpha=0.7
                )

                best_idx = np.argmax(corr_values)
                bars[best_idx].set_color("crimson")

                plt.title(
                    f"Klasyfikacja CCA dla epoki {target_freq} Hz (na podstawie {len(TARGET_CHANNELS)} kanałów)"
                )
                plt.xlabel("Referencyjne częstotliwości z bazy SSVEP [Hz]")
                plt.ylabel("Współczynnik korelacji CCA")
                plt.tight_layout()
                filepath = os.path.join("plots", "cca", filename, f"{target_freq}.png")
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                plt.savefig(filepath)
                plt.close()


if __name__ == "__main__":
    main()
