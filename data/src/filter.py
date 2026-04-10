import numpy as np
from scipy.signal import savgol_filter
from data_classes import trial_info
from consts import SG_WINDOW, SG_POLYORDER


def main(
    trials: list[trial_info], window=SG_WINDOW, polyorder=SG_POLYORDER
) -> np.ndarray:
    all_epochs = np.array([t.epoch for t in trials])
    all_filtered = np.zeros_like(all_epochs)

    for t in range(all_epochs.shape[0]):
        for ch in range(all_epochs.shape[1]):
            all_filtered[t, ch, :] = savgol_filter(
                all_epochs[t, ch, :], window, polyorder
            )

    return all_filtered
