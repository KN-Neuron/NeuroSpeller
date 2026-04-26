from eeg_streamer import EEGStreamer
from data.src.predictor import Predictor
from data.src.preprocessor import Preprocessor


class BCIEngine:
    def __init__(
        self,
        streamer: EEGStreamer,
        predictor: Predictor,
        preprocessor: Preprocessor,
    ):
        self.streamer = streamer
        self.predictor = predictor
        self.preprocessor = preprocessor

    def predict(self):
        epoch = self.streamer.get_current_window()
        epoch_preprocessed = self.preprocessor.preprocess(epoch)
        result = self.predictor.predict(epoch_preprocessed)

        return result
