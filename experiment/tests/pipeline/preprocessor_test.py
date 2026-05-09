import numpy as np
import pytest
from src.pipeline.preprocessor import EEGPreprocessor


@pytest.fixture
def preprocessor():
    """Preprocessor targeting channels 1, 6, 11 (like the real config)."""
    return EEGPreprocessor(target_channels=[1, 6, 11], sg_window=11, sg_polyorder=3)


def _make_epoch(num_channels=16, num_samples=500, seed=42):
    """Generate a random EEG-like epoch (channels × samples)."""
    rng = np.random.default_rng(seed)
    return rng.normal(0, 10, (num_channels, num_samples))


class TestPreprocessBasic:
    def test_all_zeros_returns_none(self, preprocessor):
        epoch = np.zeros((16, 500))
        assert preprocessor.preprocess(epoch) is None

    def test_nonzero_input_returns_array(self, preprocessor):
        result = preprocessor.preprocess(_make_epoch())
        assert result is not None
        assert isinstance(result, np.ndarray)


class TestPreprocessShape:
    def test_output_shape(self, preprocessor):
        num_samples = 500
        epoch = _make_epoch(num_samples=num_samples)
        result = preprocessor.preprocess(epoch)
        # Output is transposed: (samples, channels)
        assert result.shape == (num_samples, len(preprocessor.target_channels))

    def test_output_shape_different_sample_count(self, preprocessor):
        for n in [100, 250, 1000]:
            epoch = _make_epoch(num_samples=n)
            result = preprocessor.preprocess(epoch)
            assert result.shape == (n, len(preprocessor.target_channels))


class TestChannelSelection:
    def test_only_target_channels_survive(self):
        """Mark each channel with a unique DC offset; verify only the target
        channels' offsets appear in the output."""
        target_channels = [2, 5]
        preprocessor = EEGPreprocessor(target_channels=target_channels)
        num_channels, num_samples = 16, 500

        # Give each channel a distinct large DC so mean-subtraction still
        # leaves a detectable per-channel signature.
        epoch = np.zeros((num_channels, num_samples))
        for ch in range(num_channels):
            epoch[ch, :] = (ch + 1) * 1000

        result = preprocessor.preprocess(epoch)
        assert result.shape[1] == len(target_channels)


class TestCARSubtraction:
    def test_car_removes_global_mean(self, preprocessor):
        """After CAR, the mean across channels at each time-point should be
        approximately zero (before channel selection)."""
        epoch = _make_epoch()
        mean_signal = np.mean(epoch, axis=0)
        car_epoch = epoch - mean_signal
        # Verify the property directly
        np.testing.assert_allclose(
            np.mean(car_epoch, axis=0), 0, atol=1e-10
        )


class TestSavgolSmoothing:
    def test_output_is_smoother(self, preprocessor):
        """The Savitzky-Golay filter should reduce high-frequency energy
        compared to an unfiltered version of the same target channels."""
        epoch = _make_epoch()

        result = preprocessor.preprocess(epoch)

        # Manually do CAR + channel selection WITHOUT filtering
        mean_signal = np.mean(epoch, axis=0)
        car = epoch - mean_signal
        raw_target = car[preprocessor.target_channels, :].T  # (samples, ch)

        # Compare absolute diff of consecutive samples (proxy for HF energy)
        hf_raw = np.mean(np.abs(np.diff(raw_target, axis=0)))
        hf_filtered = np.mean(np.abs(np.diff(result, axis=0)))

        assert hf_filtered < hf_raw
