from scipy.signal import butter, sosfiltfilt
from typing import Optional
from abc import ABC, abstractmethod
import numpy as np


class Preprocessor(ABC):
    @abstractmethod
    def preprocess(self, epoch: np.ndarray) -> Optional[np.ndarray]:
        pass


class EEGPreprocessor(Preprocessor):
    def __init__(
        self,
        target_channels: list[int],
        sampling_rate: float = 250,
        bandpass_low: float = 4.0,
        bandpass_high: float = 45.0,
        bandpass_order: int = 4,
    ):
        self.target_channels = target_channels
        self.sampling_rate = sampling_rate

        nyquist = sampling_rate / 2.0
        high = min(bandpass_high, nyquist - 1.0)
        self.sos = butter(
            bandpass_order, [bandpass_low, high], btype="band", fs=sampling_rate, output="sos"
        )

    def preprocess(self, epoch: np.ndarray) -> Optional[np.ndarray]:
        if np.all(epoch == 0):
            return None

        mean_signal = np.mean(epoch, axis=0)
        car_epoch = epoch - mean_signal
        X_target = car_epoch[self.target_channels, :]
        X_filtered = sosfiltfilt(self.sos, X_target, axis=1)

        return X_filtered.T
