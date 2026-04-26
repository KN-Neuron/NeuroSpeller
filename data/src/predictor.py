from sklearn.cross_decomposition import CCA
from typing import Dict, Optional
from abc import ABC, abstractmethod
import numpy as np


class Predictor(ABC):
    @abstractmethod
    def predict(self, X: np.ndarray) -> Optional[float]:
        pass


class CCAPredictor(Predictor):
    def __init__(
        self,
        expected_frequencies: list[float],
        sampling_rate: float,
        window_length: int,
        threshold: float,
    ):
        self.sampling_rate = sampling_rate
        self.expected_frequencies = expected_frequencies
        self.threshold = threshold
        self.cca = CCA(n_components=1)
        self.reference_signals_dict = self._generate_reference_signals_dictionary(
            window_length
        )

    def _generate_reference_signals_for_frequency(
        self, length: int, freq: float, num_harmonics=2
    ):
        t = np.arange(length) / self.sampling_rate
        y = []
        for i in range(1, num_harmonics + 1):
            y.append(np.sin(2 * np.pi * i * freq * t))
            y.append(np.cos(2 * np.pi * i * freq * t))
        return np.array(y).T

    def _generate_reference_signals_dictionary(
        self, length: int, num_harmonics=2
    ) -> Dict[float, np.ndarray]:
        reference_dict = {}
        for frequency in self.expected_frequencies:
            reference_dict[frequency] = self._generate_reference_signals_for_frequency(
                length, frequency, num_harmonics
            )
        return reference_dict

    def predict(self, X_preprocessed: np.ndarray) -> Optional[float]:
        if X_preprocessed is None:
            return None

        best_freq = None
        max_corr = 0

        for expected_freq in self.expected_frequencies:
            Y = self.reference_signals_dict[expected_freq]

            self.cca.fit(X_preprocessed, Y)
            Xc, Yc = self.cca.transform(X_preprocessed, Y)

            corr = np.corrcoef(Xc[:, 0], Yc[:, 0])[0, 1]

            if corr > max_corr:
                max_corr = corr
                best_freq = expected_freq

        if max_corr > self.threshold:
            return best_freq

        return None
