from data_classes import trial_info
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from consts import (
    EXPECTED_FREQS,
    CHANNELS,
    FREQ_COLORS,
    SNR_THRESHOLD_DB,
    CONFIDENCE_LEVEL,
    SG_WINDOW,
    SG_POLYORDER,
    SAMPLING_RATE,
    SAMPLES_PER_5_SEC,
)

N = SAMPLES_PER_5_SEC
freqs_fft = np.fft.rfftfreq(N, d=1.0 / SAMPLING_RATE)


def plot_single_trial_fft(
    trial: trial_info,
    magnitude: np.ndarray,
    ch_idx: int,
    ch_name: str,
    snr_db: float,
    out_dir: str,
):
    """Plot FFT magnitude spectrum for a single trial + channel."""
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(freqs_fft, magnitude, color="steelblue", linewidth=1)

    target_bin = np.argmin(np.abs(freqs_fft - trial.closest_freq))
    ax.plot(
        freqs_fft[target_bin],
        magnitude[target_bin],
        "r*",
        markersize=15,
        label=f"Target: {trial.closest_freq} Hz",
    )
    ax.axvline(
        trial.closest_freq, color="red", linestyle="--", linewidth=1.5, alpha=0.7
    )

    # Mark all expected frequencies
    for ef in EXPECTED_FREQS:
        if ef != trial.closest_freq:
            ax.axvline(ef, color="gray", linestyle=":", alpha=0.4)

    # Mark harmonics
    for h in [2, 3]:
        harmonic = trial.closest_freq * h
        if harmonic < freqs_fft[-1]:
            ax.axvline(harmonic, color="orange", linestyle=":", alpha=0.5)
            ax.text(
                harmonic + 0.2,
                ax.get_ylim()[1] * 0.85,
                f"{h}×{trial.closest_freq:.1f}",
                fontsize=7,
                color="orange",
            )

    ax.text(
        0.02,
        0.95,
        f"SNR: {snr_db:.1f} dB | Target: {trial.closest_freq} Hz | True: {trial.true_freq} Hz",
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    ax.set_xlim(0, 35)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("FFT Magnitude (µV)")
    ax.set_title(
        f"Trial {trial.trial} — {ch_name} — FFT Magnitude Spectrum (Savitzky-Golay filtered)"
    )
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{out_dir}/fft_trial{trial.trial:02d}_{ch_name}.png", dpi=150)
    plt.close()


def plot_grouped_fft(
    freq: float,
    per_trial_results: list[dict],
    stats: dict,
    out_dir: str,
):
    """Plot mean ± SD FFT spectrum across repetitions for one target frequency."""
    fig, axes = plt.subplots(len(CHANNELS), 1, figsize=(14, 4 * len(CHANNELS)))
    if len(CHANNELS) == 1:
        axes = [axes]

    for ax_i, (ch_idx, ch_name) in enumerate(CHANNELS.items()):
        ax = axes[ax_i]
        ch_results = [r for r in per_trial_results if r["ch_idx"] == ch_idx]

        all_mags = []
        for r in ch_results:
            ax.plot(
                freqs_fft,
                r["magnitude"],
                color=FREQ_COLORS[freq],
                linewidth=0.5,
                alpha=0.3,
            )
            all_mags.append(r["magnitude"])

        if len(all_mags) > 0:
            all_mags_arr = np.array(all_mags)
            mean_mag = np.mean(all_mags_arr, axis=0)
            std_mag = np.std(all_mags_arr, axis=0)

            ax.plot(
                freqs_fft,
                mean_mag,
                color=FREQ_COLORS[freq],
                linewidth=2,
                label=f"Mean (n={len(ch_results)})",
            )
            ax.fill_between(
                freqs_fft,
                mean_mag - std_mag,
                mean_mag + std_mag,
                color=FREQ_COLORS[freq],
                alpha=0.2,
                label="±1 SD",
            )

            target_idx = np.argmin(np.abs(freqs_fft - freq))
            ax.axvline(freq, color="black", linestyle="--", linewidth=2, alpha=0.8)
            ax.plot(
                freq,
                mean_mag[target_idx],
                "k*",
                markersize=15,
                label=f"Target: {freq} Hz (mag={mean_mag[target_idx]:.4f})",
            )

            for h in [2, 3]:
                if freq * h < freqs_fft[-1]:
                    ax.axvline(freq * h, color="gray", linestyle=":", alpha=0.5)

            for ef2 in EXPECTED_FREQS:
                if ef2 != freq:
                    ax.axvline(ef2, color=FREQ_COLORS[ef2], linestyle="--", alpha=0.2)

        # Confidence annotation
        stat_key = f"{freq}_{ch_idx}"
        if stat_key in stats and stats[stat_key]["n_reps"] >= 2:
            s = stats[stat_key]
            conf_text = (
                f"SNR: {s['mean_snr_db']:.1f} dB "
                f"[{s['ci_snr_low']:.1f}, {s['ci_snr_high']:.1f}] "
                f"{'✓ CONFIDENT' if s['is_confident'] else '✗ NOT confident'}"
            )
            ax.text(
                0.02,
                0.95,
                conf_text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
            )

        ax.set_xlim(0, 35)
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("FFT Magnitude (µV)")
        ax.set_title(f"{ch_name} — Target: {freq} Hz")
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)

    plt.suptitle(
        f"FFT Spectrum — Target: {freq} Hz — Test trials ± confidence\n"
        f"(Savitzky-Golay: window={SG_WINDOW}, order={SG_POLYORDER})",
        fontsize=13,
    )
    plt.tight_layout()
    plt.savefig(f"{out_dir}/fft_{freq:.2f}Hz.png", dpi=150)
    plt.close()


def plot_snr_heatmap(stats: dict, out_dir: str):
    """Plot SNR heatmap (frequency × channel)."""
    fig, ax = plt.subplots(figsize=(10, 6))

    ch_names = list(CHANNELS.values())
    snr_matrix = np.zeros((len(EXPECTED_FREQS), len(ch_names)))
    conf_matrix = np.zeros((len(EXPECTED_FREQS), len(ch_names)), dtype=bool)

    for ef_i, ef in enumerate(EXPECTED_FREQS):
        for ch_j, (ch_idx, ch_name) in enumerate(CHANNELS.items()):
            key = f"{ef}_{ch_idx}"
            if key in stats:
                snr_matrix[ef_i, ch_j] = stats[key]["mean_snr_db"]
                conf_matrix[ef_i, ch_j] = stats[key]["is_confident"]

    im = ax.imshow(
        snr_matrix,
        cmap="RdYlGn",
        aspect="auto",
        vmin=0,
        vmax=max(20, np.max(snr_matrix)),
    )

    for i in range(len(EXPECTED_FREQS)):
        for j in range(len(ch_names)):
            marker = "✓" if conf_matrix[i, j] else "✗"
            ax.text(
                j,
                i,
                f"{snr_matrix[i, j]:.1f} dB\n{marker}",
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold" if conf_matrix[i, j] else "normal",
            )

    ax.set_xticks(range(len(ch_names)))
    ax.set_xticklabels(ch_names)
    ax.set_yticks(range(len(EXPECTED_FREQS)))
    ax.set_yticklabels([f"{ef} Hz" for ef in EXPECTED_FREQS])
    ax.set_title(
        f"SNR Heatmap — Threshold: {SNR_THRESHOLD_DB:.2f} dB\n"
        f"✓ = {CONFIDENCE_LEVEL * 100:.0f}% CI lower bound > threshold"
    )
    plt.colorbar(im, label="SNR (dB)")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/snr_heatmap.png", dpi=150)
    plt.close()
