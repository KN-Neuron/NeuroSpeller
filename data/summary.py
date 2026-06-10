import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch, butter, sosfiltfilt
from sklearn.cross_decomposition import CCA
from loader import load_data
from plots import plot_time_series, plot_fft, plot_psd

from experiment.src.config.bci_config import (
    SAMPLING_RATE,
    TARGET_CHANNELS,
    FREQS,
    WINDOW_TIME_FRAME,
    BANDPASS_LOW,
    BANDPASS_HIGH,
    BANDPASS_ORDER,
    NUM_HARMONICS,
)
from experiment.src.pipeline.predictor import CCAPredictor, FBCCAPredictor


def create_bandpass_filter(low, high, fs, order=4):
    """Create a Butterworth bandpass filter."""
    nyquist = fs / 2.0
    high = min(high, nyquist - 1.0)
    return butter(order, [low, high], btype="band", fs=fs, output="sos")


def main():
    filenames = [
        "kacper/kacper1.fif",
        "kacper/kacper2.fif",
        "kacper/kacper3.fif",
    ]

    # Design bandpass filter for preprocessing
    sos_bandpass = create_bandpass_filter(
        BANDPASS_LOW, BANDPASS_HIGH, SAMPLING_RATE, BANDPASS_ORDER
    )

    # Track predictions for confusion matrix
    all_results_cca = []     # (true_freq, predicted_freq_or_None)
    all_results_fbcca = []

    for filename in filenames:
        print(f"\n{'='*60}\nPrzetwarzanie pliku: {filename}\n{'='*60}")
        data_dict = load_data(
            filename, target_marker_freqs=FREQS, l_freq=BANDPASS_LOW, h_freq=BANDPASS_HIGH
        )

        if data_dict is None:
            continue

        # Iteracja po słowniku z wyizolowanymi epokami dla każdej częstotliwości
        for target_freq, epoch_data in data_dict.items():
            print(f"\n--- Analiza dla częstotliwości docelowej: {target_freq} Hz ---")

            # Zabezpieczenie na wypadek, gdyby epoki nie pobrano prawidłowo
            if epoch_data.ndim < 2:
                print(f"Pominięto {target_freq} Hz (brak danych).")
                continue

            num_samples = epoch_data.shape[1]
            time = np.linspace(0, WINDOW_TIME_FRAME, num_samples, endpoint=False)

            # === PREPROCESSING ===
            # 1. CAR (Common Average Reference) — using ALL channels
            mean_signal = np.mean(epoch_data, axis=0)
            car_all_channels = epoch_data - mean_signal

            # 2. Bandpass filter
            filtered_all_channels = sosfiltfilt(sos_bandpass, car_all_channels, axis=1)

            # Analiza per kanał (Time Series, FFT, PSD)
            for ch_idx in TARGET_CHANNELS:
                print(f"  -> Rysowanie wykresów dla kanału nr {ch_idx}")

                raw_signal = epoch_data[ch_idx, :]
                car_signal = car_all_channels[ch_idx, :]
                filtered_signal = filtered_all_channels[ch_idx, :]

                # 1. Wykres w dziedzinie czasu
                plot_time_series(
                    time, raw_signal, car_signal, filtered_signal, ch_idx
                )
                filepath = os.path.join(
                    "plots", "time_series", filename, str(ch_idx), f"{target_freq}.png"
                )
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                plt.savefig(filepath)
                plt.close()

                # 2. Wykres FFT
                plt.figure(figsize=(12, 6))
                plot_fft(raw_signal, "Przed filtrem", "gray")
                plot_fft(car_signal, "Po CAR", "blue")
                plot_fft(filtered_signal, "Po filtrze Bandpass", "red")
                plt.title(
                    f"Analiza częstotliwości FFT - Kanał {ch_idx} (Bodziec: {target_freq} Hz)"
                )

                # Mark target frequency and its harmonics
                for h in range(1, NUM_HARMONICS + 1):
                    plt.axvline(
                        x=target_freq * h,
                        color="green",
                        linestyle="--",
                        alpha=0.5,
                        label=f"Harmoniczna {h}x ({target_freq * h} Hz)" if h <= 3 else None,
                    )
                plt.legend()

                filepath = os.path.join(
                    "plots", "fft", filename, str(ch_idx), f"{target_freq}.png"
                )
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                plt.savefig(filepath)
                plt.close()

                # 3. Wykres PSD (Welch)
                nperseg = min(2 * SAMPLING_RATE, len(raw_signal))
                f_raw, psd_raw = welch(raw_signal, fs=SAMPLING_RATE, nperseg=nperseg)
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

            # === CLASSIFICATION ===
            # Prepare input: target channels, bandpass filtered, transposed
            epoch_X = filtered_all_channels[TARGET_CHANNELS, :].T

            # --- Standard CCA ---
            print("  -> Klasyfikacja CCA (standard)")
            cca_predictor = CCAPredictor(
                expected_frequencies=FREQS,
                sampling_rate=SAMPLING_RATE,
                window_length=num_samples,
                threshold=0.0,  # No threshold for analysis — see all correlations
                num_harmonics=NUM_HARMONICS,
            )
            cca_predicted = cca_predictor.predict(epoch_X)
            print(f"     Predykcja CCA: {cca_predicted} Hz (target: {target_freq} Hz)")
            print(f"     Korelacje CCA: {cca_predictor.last_correlations}")
            all_results_cca.append((target_freq, cca_predicted))

            # CCA bar plot
            freqs_list = list(cca_predictor.last_correlations.keys())
            corr_values = list(cca_predictor.last_correlations.values())
            _plot_cca_bars(
                freqs_list, corr_values, target_freq,
                f"CCA (standard, {NUM_HARMONICS} harmonicznych) — Target: {target_freq} Hz",
                os.path.join("plots", "cca", filename, f"{target_freq}.png"),
            )

            # --- FBCCA ---
            print("  -> Klasyfikacja FBCCA")
            fbcca_predictor = FBCCAPredictor(
                expected_frequencies=FREQS,
                sampling_rate=SAMPLING_RATE,
                window_length=num_samples,
                threshold=0.0,
                num_harmonics=NUM_HARMONICS,
            )
            fbcca_predicted = fbcca_predictor.predict(epoch_X)
            print(f"     Predykcja FBCCA: {fbcca_predicted} Hz (target: {target_freq} Hz)")
            print(f"     Scores FBCCA: {fbcca_predictor.last_correlations}")
            all_results_fbcca.append((target_freq, fbcca_predicted))

            # FBCCA bar plot
            fbcca_freqs = list(fbcca_predictor.last_correlations.keys())
            fbcca_scores = list(fbcca_predictor.last_correlations.values())
            _plot_cca_bars(
                fbcca_freqs, fbcca_scores, target_freq,
                f"FBCCA (Filter Bank CCA) — Target: {target_freq} Hz",
                os.path.join("plots", "fbcca", filename, f"{target_freq}.png"),
            )

    # === SUMMARY: Accuracy and Confusion Matrix ===
    print("\n" + "=" * 60)
    print("PODSUMOWANIE KLASYFIKACJI")
    print("=" * 60)

    _print_accuracy_table("Standard CCA", all_results_cca)
    _print_accuracy_table("FBCCA", all_results_fbcca)

    _plot_confusion_matrix("Standard CCA", all_results_cca, "plots/confusion_cca.png")
    _plot_confusion_matrix("FBCCA", all_results_fbcca, "plots/confusion_fbcca.png")


def _plot_cca_bars(freqs_list, corr_values, target_freq, title, filepath):
    """Plot CCA/FBCCA correlation bar chart."""
    plt.figure(figsize=(10, 5))
    colors = []
    for f in freqs_list:
        if f == target_freq:
            colors.append("forestgreen")  # True target
        else:
            colors.append("teal")

    bars = plt.bar([str(f) for f in freqs_list], corr_values, color=colors, alpha=0.8)

    # Highlight the winner (predicted)
    best_idx = np.argmax(corr_values)
    if freqs_list[best_idx] != target_freq:
        bars[best_idx].set_edgecolor("crimson")
        bars[best_idx].set_linewidth(3)

    plt.title(title)
    plt.xlabel("Referencyjne częstotliwości z bazy SSVEP [Hz]")
    plt.ylabel("Korelacja / Score")
    plt.tight_layout()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    plt.savefig(filepath)
    plt.close()


def _print_accuracy_table(name, results):
    """Print per-frequency and overall accuracy."""
    print(f"\n--- {name} ---")
    correct = 0
    per_freq = {}

    for true_f, pred_f in results:
        if true_f not in per_freq:
            per_freq[true_f] = {"correct": 0, "total": 0}
        per_freq[true_f]["total"] += 1

        if pred_f == true_f:
            correct += 1
            per_freq[true_f]["correct"] += 1

    total = len(results)
    print(f"  Overall: {correct}/{total} = {100 * correct / total:.1f}%")
    for freq in sorted(per_freq.keys()):
        d = per_freq[freq]
        acc = 100 * d["correct"] / d["total"] if d["total"] > 0 else 0
        print(f"  {freq:6.2f} Hz: {d['correct']}/{d['total']} = {acc:.0f}%")


def _plot_confusion_matrix(name, results, filepath):
    """Plot and save confusion matrix."""
    freq_labels = sorted(set(f for f, _ in results))
    n = len(freq_labels)
    freq_to_idx = {f: i for i, f in enumerate(freq_labels)}

    matrix = np.zeros((n, n), dtype=int)
    no_prediction = np.zeros(n, dtype=int)

    for true_f, pred_f in results:
        if pred_f is not None and pred_f in freq_to_idx:
            matrix[freq_to_idx[true_f], freq_to_idx[pred_f]] += 1
        else:
            no_prediction[freq_to_idx[true_f]] += 1

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(matrix, cmap="YlGnBu", aspect="auto")

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels([f"{f} Hz" for f in freq_labels], rotation=45)
    ax.set_yticklabels([f"{f} Hz" for f in freq_labels])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True Target")
    ax.set_title(f"Confusion Matrix — {name}")

    # Annotate cells
    for i in range(n):
        for j in range(n):
            color = "white" if matrix[i, j] > matrix.max() / 2 else "black"
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center", color=color, fontsize=14)

    plt.colorbar(im)
    plt.tight_layout()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    plt.savefig(filepath)
    plt.close()
    print(f"  Confusion matrix saved: {filepath}")


if __name__ == "__main__":
    main()
