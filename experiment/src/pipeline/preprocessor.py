from scipy.signal import savgol_filter
from typing import Optional
from abc import ABC, abstractmethod
import numpy as np


class Preprocessor(ABC):
    @abstractmethod
    def preprocess(self, epoch: np.ndarray) -> Optional[np.ndarray]:
        pass


class EEGPreprocessor(Preprocessor):
    def __init__(
        self, target_channels: list[int], sg_window: int = 11, sg_polyorder: int = 3
    ):
        self.target_channels = target_channels
        self.sg_window = sg_window
        self.sg_polyorder = sg_polyorder

    def preprocess(self, epoch: np.ndarray) -> Optional[np.ndarray]:
        if np.all(epoch == 0):
            return None

        mean_signal = np.mean(epoch, axis=0)
        car_epoch = epoch - mean_signal
        X_target = car_epoch[self.target_channels, :]
        X_filtered = savgol_filter(
            X_target, window_length=self.sg_window, polyorder=self.sg_polyorder, axis=1
        )

        # Transpose to shape (samples, channels) for CCA
        return X_filtered.T
