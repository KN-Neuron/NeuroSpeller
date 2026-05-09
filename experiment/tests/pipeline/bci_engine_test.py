import numpy as np
import pytest
from unittest.mock import MagicMock, call
from src.pipeline.bci_engine import BCIEngine


@pytest.fixture
def mock_components():
    streamer = MagicMock()
    preprocessor = MagicMock()
    predictor = MagicMock()
    return streamer, preprocessor, predictor


@pytest.fixture
def engine(mock_components):
    streamer, preprocessor, predictor = mock_components
    return BCIEngine(
        streamer=streamer,
        preprocessor=preprocessor,
        predictor=predictor,
    )


class TestPipelineWiring:
    def test_predict_calls_pipeline_in_order(self, engine, mock_components):
        """Streamer -> Preprocessor -> Predictor must be called in sequence."""
        streamer, preprocessor, predictor = mock_components
        raw = np.ones((16, 500))
        processed = np.ones((500, 3))

        streamer.get_current_window.return_value = raw
        preprocessor.preprocess.return_value = processed
        predictor.predict.return_value = 10.0

        engine.predict()

        streamer.get_current_window.assert_called_once()
        preprocessor.preprocess.assert_called_once()
        predictor.predict.assert_called_once()

    def test_predict_passes_preprocessed_data(self, engine, mock_components):
        """The preprocessor's output must be forwarded to the predictor."""
        streamer, preprocessor, predictor = mock_components
        raw = np.ones((16, 500))
        processed = np.ones((500, 3)) * 42

        streamer.get_current_window.return_value = raw
        preprocessor.preprocess.return_value = processed
        predictor.predict.return_value = 10.0

        engine.predict()

        actual_preprocess_arg = preprocessor.preprocess.call_args[0][0]
        np.testing.assert_array_equal(actual_preprocess_arg, raw)

        actual_predict_arg = predictor.predict.call_args[0][0]
        np.testing.assert_array_equal(actual_predict_arg, processed)

    def test_predict_returns_predictor_result(self, engine, mock_components):
        streamer, preprocessor, predictor = mock_components
        streamer.get_current_window.return_value = np.zeros((16, 500))
        preprocessor.preprocess.return_value = np.zeros((500, 3))
        predictor.predict.return_value = 12.0

        result = engine.predict()
        assert result == 12.0

    def test_predict_returns_none_when_predictor_returns_none(
        self, engine, mock_components
    ):
        streamer, preprocessor, predictor = mock_components
        streamer.get_current_window.return_value = np.zeros((16, 500))
        preprocessor.preprocess.return_value = None
        predictor.predict.return_value = None

        result = engine.predict()
        assert result is None
