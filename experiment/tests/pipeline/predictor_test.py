import numpy as np
import pytest
from src.pipeline.predictor import CCAPredictor


FREQUENCIES = [7.0, 10.0, 12.0, 15.0]
SAMPLING_RATE = 250.0
WINDOW_LENGTH = 500


@pytest.fixture
def predictor():
    return CCAPredictor(
        expected_frequencies=FREQUENCIES,
        sampling_rate=SAMPLING_RATE,
        window_length=WINDOW_LENGTH,
        threshold=0.3,
    )


def _make_sine_signal(freq, sampling_rate=SAMPLING_RATE, length=WINDOW_LENGTH,
                      num_channels=3, amplitude=10.0, noise_std=0.5, seed=42):
    """Create a (length, num_channels) array with a clean sine + mild noise."""
    rng = np.random.default_rng(seed)
    t = np.arange(length) / sampling_rate
    signal = amplitude * np.sin(2 * np.pi * freq * t)
    data = np.column_stack([signal] * num_channels)
    data += rng.normal(0, noise_std, data.shape)
    return data


class TestReferenceSignals:
    def test_dictionary_keys(self, predictor):
        assert set(predictor.reference_signals_dict.keys()) == set(FREQUENCIES)

    def test_reference_shape(self, predictor):
        num_harmonics = 2
        for freq, ref in predictor.reference_signals_dict.items():
            assert ref.shape == (WINDOW_LENGTH, 2 * num_harmonics)

    def test_reference_values_are_bounded(self, predictor):
        """Sine/cosine values should be in [-1, 1]."""
        for ref in predictor.reference_signals_dict.values():
            assert np.all(ref >= -1.0 - 1e-10)
            assert np.all(ref <= 1.0 + 1e-10)


class TestNoneInput:
    def test_none_input_returns_none(self, predictor):
        assert predictor.predict(None) is None


class TestFrequencyDetection:
    @pytest.mark.parametrize("target_freq", FREQUENCIES)
    def test_detects_known_frequency(self, predictor, target_freq):
        signal = _make_sine_signal(target_freq)
        result = predictor.predict(signal)
        assert result == target_freq

    def test_below_threshold_returns_none(self):
        predictor = CCAPredictor(
            expected_frequencies=FREQUENCIES,
            sampling_rate=SAMPLING_RATE,
            window_length=WINDOW_LENGTH,
            threshold=0.99,  # impossibly high
        )
        noise = np.random.default_rng(0).normal(0, 1, (WINDOW_LENGTH, 3))
        assert predictor.predict(noise) is None

    def test_distinguishes_frequencies(self, predictor):
        """Each frequency's sine should map to the correct label."""
        for freq in FREQUENCIES:
            signal = _make_sine_signal(freq, seed=int(freq * 10))
            assert predictor.predict(signal) == freq
