import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import welch
import os

from consts import (
    SAMPLING_RATE,
    SAMPLES_PER_5_SEC,
    EXPECTED_FREQS,
    CHANNELS_TIME,
    SG_WINDOW,
    SG_POLYORDER,
    OUTPUT_DIR,
)
from data_classes import trial_info, TrialType


def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def plot_time_domain(
    trials: list[trial_info],
    raw_epochs: np.ndarray,
    filtered_epochs: np.ndarray,
):
    """Plot raw vs Savitzky-Golay filtered signal for each test trial × channel."""
    _ensure_output_dir()
    time_axis = np.linspace(0, 5, SAMPLES_PER_5_SEC)

    for t_idx, trial in enumerate(trials):
        if trial.type != TrialType.TEST:
            continue

        for ch_idx, ch_name in CHANNELS_TIME.items():
            raw_signal = raw_epochs[t_idx, ch_idx, :]
            filt_signal = filtered_epochs[t_idx, ch_idx, :]

            fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)

            axes[0].plot(time_axis, raw_signal, "b-", linewidth=0.5)
            axes[0].set_title(
                f"Test Trial {trial.trial} — {ch_name} — "
                f"{trial.true_freq} Hz (≈{trial.closest_freq} Hz) — RAW"
            )
            axes[0].set_ylabel("Amplitude (µV)")
            axes[0].grid(True, alpha=0.3)

            axes[1].plot(time_axis, filt_signal, "r-", linewidth=0.8)
            axes[1].set_title(
                f"Savitzky-Golay (window={SG_WINDOW}, order={SG_POLYORDER})"
            )
            axes[1].set_xlabel("Time (seconds)")
            axes[1].set_ylabel("Amplitude (µV)")
            axes[1].grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig(
                f"{OUTPUT_DIR}/time_Trial{trial.trial:02d}_{ch_name}.png", dpi=150
            )
            plt.close()

        print(f"  Time plots: trial {trial.trial}")


def plot_psd_comparison(
    trials: list[trial_info],
    raw_epochs: np.ndarray,
    filtered_epochs: np.ndarray,
):
    """Plot PSD comparison (raw vs filtered) for each test trial × channel."""
    _ensure_output_dir()

    for t_idx, trial in enumerate(trials):
        if trial.type != TrialType.TEST:
            continue

        for ch_idx, ch_name in CHANNELS_TIME.items():
            raw_signal = raw_epochs[t_idx, ch_idx, :]
            filt_signal = filtered_epochs[t_idx, ch_idx, :]

            freqs_raw, psd_raw = welch(
                raw_signal, fs=SAMPLING_RATE, nperseg=SAMPLES_PER_5_SEC
            )
            freqs_filt, psd_filt = welch(
                filt_signal, fs=SAMPLING_RATE, nperseg=SAMPLES_PER_5_SEC
            )

            fig, ax = plt.subplots(figsize=(12, 5))
            ax.semilogy(freqs_raw, psd_raw, "b-", linewidth=1, alpha=0.7, label="Raw")
            ax.semilogy(
                freqs_filt, psd_filt, "r-", linewidth=1.2, label="Savitzky-Golay"
            )

            for ef in EXPECTED_FREQS:
                ax.axvline(ef, color="green", linestyle="--", alpha=0.4, linewidth=1)
            if trial.closest_freq > 0:
                ax.axvline(
                    trial.closest_freq,
                    color="green",
                    linestyle="-",
                    alpha=0.8,
                    linewidth=2,
                    label=f"Expected: {trial.closest_freq} Hz",
                )

            ax.set_xlim(2, 35)
            ax.set_xlabel("Frequency (Hz)")
            ax.set_ylabel("PSD (µV²/Hz)")
            ax.set_title(f"Test Trial {trial.trial} — {ch_name} — PSD: Raw vs Filtered")
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.savefig(
                f"{OUTPUT_DIR}/psd_Trial{trial.trial:02d}_{ch_name}.png", dpi=150
            )
            plt.close()

        print(f"  PSD plots: trial {trial.trial}")
