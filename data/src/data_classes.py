import numpy as np
from enum import Enum


class TrialType(Enum):
    ADAPT = 0
    TEST = 1


class trial_group:
    def __init__(
        self, start_sample: int, end_sample: int, start_idx: int, end_idx: int
    ):
        self.start_sample = start_sample
        self.end_sample = end_sample
        self.start_idx = start_idx
        self.end_idx = end_idx


class trial_info:
    def __init__(
        self,
        epoch: np.ndarray,
        trial: int,
        true_freq: float,
        closest_freq: float,
        n_dins: int,
        type: TrialType,
    ):
        self.epoch = epoch
        self.trial = trial
        self.true_freq = true_freq
        self.closest_freq = closest_freq
        self.n_dins = n_dins
        self.type = type
