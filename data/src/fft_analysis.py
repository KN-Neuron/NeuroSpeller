import numpy as np
from scipy.stats import t as t_dist
from collections import defaultdict

from consts import (
    SAMPLING_RATE,
    WINDOW_TIME_FRAME,
    SNR_NEIGHBOR_BINS,
    SNR_EXCLUDE_BINS,
    SNR_THRESHOLD_DB,
    SNR_THRESHOLD_LINEAR,
    EXPECTED_FREQS,
    CHANNELS,
    CONFIDENCE_LEVEL,
)
from data_classes import trial_info, TrialType
from utils import group_trials_by_frequency, get_trials_by_type

samples_per_trial = SAMPLING_RATE * WINDOW_TIME_FRAME
freqs_fft = np.fft.rfftfreq(samples_per_trial, d=1.0 / SAMPLING_RATE)


def compute_rfft(signal: np.ndarray) -> np.ndarray:
    signal_centered = signal - np.mean(signal)
    return np.fft.rfft(signal_centered)


def compute_fft_magnitude(signal: np.ndarray) -> np.ndarray:
    fft_result = compute_rfft(signal)
    magnitude = (2.0 / samples_per_trial) * np.abs(fft_result)
    return magnitude


def compute_snr(magnitude: np.ndarray, target_freq: float) -> tuple[float, float, int]:
    target_bin = np.argmin(np.abs(freqs_fft - target_freq))
    signal_power = magnitude[target_bin] ** 2

    left_slice = magnitude[
        max(0, target_bin - SNR_NEIGHBOR_BINS - SNR_EXCLUDE_BINS) : target_bin
        - SNR_EXCLUDE_BINS
    ]
    right_slice = magnitude[
        target_bin
        + SNR_EXCLUDE_BINS
        + 1 : target_bin
        + SNR_NEIGHBOR_BINS
        + SNR_EXCLUDE_BINS
        + 1
    ]

    noise_bins = np.concatenate([left_slice, right_slice])
    noise_power = np.mean(noise_bins**2) if len(noise_bins) > 0 else 1e-12

    snr_linear = signal_power / noise_power if noise_power > 0 else float("inf")
    snr_db = 10 * np.log10(snr_linear) if snr_linear > 0 else float("inf")
    return snr_linear, snr_db, target_bin


def compute_confidence_intervals(
    snr_db_values: list[float],
    peak_values: list[float],
    confidence_level: float = CONFIDENCE_LEVEL,
) -> dict:
    n_reps = len(snr_db_values)

    if n_reps < 2:
        return {
            "mean_snr_db": snr_db_values[0] if n_reps == 1 else 0,
            "ci_snr_low": float("-inf"),
            "ci_snr_high": float("inf"),
            "mean_peak": peak_values[0] if n_reps == 1 else 0,
            "ci_peak_low": 0,
            "ci_peak_high": 0,
            "is_confident": False,
            "n_reps": n_reps,
        }

    mean_snr = np.mean(snr_db_values)
    std_snr = np.std(snr_db_values, ddof=1)
    se_snr = std_snr / np.sqrt(n_reps)

    mean_peak = np.mean(peak_values)
    std_peak = np.std(peak_values, ddof=1)
    se_peak = std_peak / np.sqrt(n_reps)

    t_crit = t_dist.ppf((1 + confidence_level) / 2, df=n_reps - 1)

    ci_snr_low = mean_snr - t_crit * se_snr
    ci_snr_high = mean_snr + t_crit * se_snr
    ci_peak_low = mean_peak - t_crit * se_peak
    ci_peak_high = mean_peak + t_crit * se_peak

    is_confident = ci_snr_low > SNR_THRESHOLD_DB

    return {
        "mean_snr_db": mean_snr,
        "ci_snr_low": ci_snr_low,
        "ci_snr_high": ci_snr_high,
        "mean_peak": mean_peak,
        "ci_peak_low": ci_peak_low,
        "ci_peak_high": ci_peak_high,
        "is_confident": is_confident,
        "n_reps": n_reps,
    }


def main(trials: list[trial_info]) -> dict:
    test_trials = get_trials_by_type(trials, TrialType.TEST)
    test_by_freq = group_trials_by_frequency(test_trials)

    all_results = defaultdict(list)

    for ef in EXPECTED_FREQS:
        for trial in test_by_freq.get(ef, []):
            for ch_idx, ch_name in CHANNELS.items():
                signal = trial.epoch[ch_idx, :]
                magnitude = compute_fft_magnitude(signal)
                snr_linear, snr_db, target_bin = compute_snr(magnitude, ef)

                all_results[ef].append(
                    {
                        "trial": trial.trial,
                        "channel": ch_name,
                        "ch_idx": ch_idx,
                        "magnitude": magnitude,
                        "snr_linear": snr_linear,
                        "snr_db": snr_db,
                        "target_bin": target_bin,
                        "peak_mag": magnitude[target_bin],
                        "is_confident": snr_linear >= SNR_THRESHOLD_LINEAR,
                    }
                )
    stats = {}

    for ef in EXPECTED_FREQS:
        for ch_idx, ch_name in CHANNELS.items():
            ch_results = [r for r in all_results[ef] if r["ch_idx"] == ch_idx]
            snr_db_vals = [r["snr_db"] for r in ch_results]
            peak_vals = [r["peak_mag"] for r in ch_results]

            ci = compute_confidence_intervals(snr_db_vals, peak_vals)

            key = f"{ef}_{ch_idx}"
            stats[key] = {**ci, "freq": ef, "channel": ch_name, "ch_idx": ch_idx}

    return {
        "trials": trials,
        "all_results": dict(all_results),
        "stats": stats,
    }
