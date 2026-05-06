from experiment.src.headset.streamer import Streamer
from experiment.src.pipeline.predictor import Predictor
from experiment.src.pipeline.preprocessor import Preprocessor


class BCIEngine:
    def __init__(
        self,
        streamer: Streamer,
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
