from sklearn.cross_decomposition import CCA
from scipy.signal import butter, sosfiltfilt
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
        num_harmonics: int = 4,
    ):
        self.sampling_rate = sampling_rate
        self.expected_frequencies = expected_frequencies
        self.threshold = threshold
        self.num_harmonics = num_harmonics
        self.cca = CCA(n_components=1)
        self.reference_signals_dict = self._generate_reference_signals_dictionary(
            window_length
        )
        self.last_correlations: Dict[float, float] = {}
        self.max_correlation: Optional[float] = None

    def _generate_reference_signals_for_frequency(
        self, length: int, freq: float
    ) -> np.ndarray:
        t = np.arange(length) / self.sampling_rate
        y = []
        for i in range(1, self.num_harmonics + 1):
            y.append(np.sin(2 * np.pi * i * freq * t))
            y.append(np.cos(2 * np.pi * i * freq * t))
        return np.array(y).T

    def _generate_reference_signals_dictionary(
        self, length: int
    ) -> Dict[float, np.ndarray]:
        reference_dict = {}
        for frequency in self.expected_frequencies:
            reference_dict[frequency] = self._generate_reference_signals_for_frequency(
                length, frequency
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
            self.last_correlations[expected_freq] = corr

            if corr > max_corr:
                max_corr = corr
                best_freq = expected_freq

        self.max_correlation = max_corr

        if max_corr > self.threshold:
            return best_freq

        return None


class FBCCAPredictor(Predictor):
    def __init__(
        self,
        expected_frequencies: list[float],
        sampling_rate: float,
        window_length: int,
        threshold: float = 0.3,
        num_subbands: int = 5,
        num_harmonics: int = 4,
    ):
        self.sampling_rate = sampling_rate
        self.expected_frequencies = expected_frequencies
        self.threshold = threshold
        self.num_subbands = num_subbands
        self.num_harmonics = num_harmonics

        self.weights = np.array(
            [(n + 1) ** (-1.25) + 0.25 for n in range(num_subbands)]
        )
        self.filter_banks = self._create_filter_banks()
        self.reference_signals = self._generate_all_references(window_length)

        self.last_correlations: Dict[float, float] = {}
        self.max_correlation: Optional[float] = None

    def _create_filter_banks(self) -> list:
        """Create bandpass filters for each sub-band.
        Sub-band k covers: [k * min_freq, high_cutoff] Hz
        """
        banks = []
        min_freq = min(self.expected_frequencies)
        nyquist = self.sampling_rate / 2.0
        high_cutoff = min(nyquist - 1.0, 45.0)

        for k in range(self.num_subbands):
            low = min_freq * (k + 1)
            if low >= high_cutoff:
                break
            sos = butter(
                6, [low, high_cutoff], btype="band", fs=self.sampling_rate, output="sos"
            )
            banks.append(sos)
        return banks

    def _generate_reference_for_freq(
        self, length: int, freq: float
    ) -> np.ndarray:
        t = np.arange(length) / self.sampling_rate
        y = []
        for i in range(1, self.num_harmonics + 1):
            y.append(np.sin(2 * np.pi * i * freq * t))
            y.append(np.cos(2 * np.pi * i * freq * t))
        return np.array(y).T

    def _generate_all_references(
        self, length: int
    ) -> Dict[float, np.ndarray]:
        refs = {}
        for freq in self.expected_frequencies:
            refs[freq] = self._generate_reference_for_freq(length, freq)
        return refs

    def predict(self, X_preprocessed: np.ndarray) -> Optional[float]:
        if X_preprocessed is None:
            return None

        best_freq = None
        max_score = 0.0

        for freq in self.expected_frequencies:
            total_score = 0.0
            Y = self.reference_signals[freq]

            for k, sos in enumerate(self.filter_banks):
                # Filter signal through sub-band k
                X_filtered = sosfiltfilt(sos, X_preprocessed, axis=0)

                # CCA between filtered signal and reference
                cca = CCA(n_components=1)
                cca.fit(X_filtered, Y)
                Xc, Yc = cca.transform(X_filtered, Y)

                corr = np.corrcoef(Xc[:, 0], Yc[:, 0])[0, 1]
                # Weighted squared correlation
                total_score += self.weights[k] * (corr**2)

            self.last_correlations[freq] = total_score

            if total_score > max_score:
                max_score = total_score
                best_freq = freq

        self.max_correlation = max_score

        if max_score > self.threshold:
            return best_freq

        return None
