import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

plt.rcParams["figure.figsize"] = (12, 6)
plt.style.use("seaborn-v0_8-darkgrid")


def plot_time_series(
    time, raw_signal, car_signal, filtered_signal, ch_idx
):
    plt.figure(figsize=(12, 6))

    plt.plot(time, raw_signal, label="Sygnał Surowy (Raw)", alpha=0.5, color="gray")
    plt.plot(time, car_signal, label="Sygnał po CAR", alpha=0.5, color="blue")
    plt.plot(
        time,
        filtered_signal,
        label=f"Bandpass Filter",
        linewidth=1.5,
        color="red",
    )

    plt.title(f"Cała wyodrębniona epoka stymulacji (Kanał {ch_idx})")
    plt.xlabel("Czas względny stymulacji [s]")
    plt.ylabel("Amplituda [V]")
    plt.legend()
    plt.tight_layout()


def plot_fft(signal, title, color, sampling_rate=250):
    # Obliczanie widma amplitudowego
    N = len(signal)
    signal_fft = fft(signal)
    freqs = fftfreq(N, 1 / sampling_rate)

    # Bierzemy pod uwagę tylko częstotliwości dodatnie
    pos_mask = freqs > 0
    freqs = freqs[pos_mask]
    amplitudes = np.abs(signal_fft[pos_mask]) / N

    # Zawężanie widma do SSVEP
    mask_ssvep = freqs <= 40

    plt.plot(
        freqs[mask_ssvep], amplitudes[mask_ssvep], label=title, color=color, alpha=0.8
    )
    plt.xlabel("Częstotliwość (Hz)")
    plt.ylabel("Amplituda")
    plt.legend()
    plt.tight_layout()


def plot_psd(f_raw, psd_raw, f_filt, psd_filt):
    # Widmo SSVEP max 40 Hz
    plot_range_raw = f_raw <= 40
    plot_range_filt = f_filt <= 40

    plt.figure(figsize=(12, 6))
    plt.semilogy(
        f_raw[plot_range_raw],
        psd_raw[plot_range_raw],
        label="Surowy Sygnał",
        color="blue",
        alpha=0.5,
    )
    plt.semilogy(
        f_filt[plot_range_filt],
        psd_filt[plot_range_filt],
        label=f"Filtrowany Sygnał (Bandpass)",
        color="red",
        linewidth=1.5,
    )

    plt.title(
        "Power Spectral Density (Spodziewane potężne 'piki' przy targetach SSVEP)"
    )
    plt.xlabel("Częstotliwość [Hz]")
    plt.ylabel("PSD [V^2/Hz]")
    plt.legend()
    plt.tight_layout()
