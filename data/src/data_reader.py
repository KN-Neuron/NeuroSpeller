from collections import defaultdict
import scipy.io
from data_classes import *
from consts import (
    EEG_KEY,
    DIN_KEY,
    SAMPLING_RATE,
    EXPECTED_FREQS,
    ADAPT_TRIALS,
    WINDOW_TIME_FRAME,
)
from abc import ABC, abstractmethod


class DataReader(ABC):
    @abstractmethod
    def _load_data(self, filename: str) -> tuple[np.ndarray, np.ndarray, list[int]]:
        pass

    @abstractmethod
    def get_all_trials(self, filename: str) -> list[trial_info]:
        pass


class MatDataReader(DataReader):
    def _load_data(
        filename: str, sampling_rate: int = SAMPLING_RATE
    ) -> tuple[np.ndarray, np.ndarray, list[int]]:
        mat_data = scipy.io.loadmat(filename)
        eeg_data = mat_data[EEG_KEY]
        din_data = mat_data[DIN_KEY]

        latencies_ms = [int(din_data[1, i].item()) for i in range(din_data.shape[1])]
        latencies = [int(round(l * sampling_rate / 1000)) for l in latencies_ms]

        return eeg_data, latencies_ms, latencies

    def _group_din_markers_into_trials(
        latencies: list[int], gap_threshold_samples: int
    ) -> list[trial_group]:
        trial_groups = []
        current_start_idx = 0
        current_group_start = latencies[0]
        current_group_end = latencies[0]

        for i in range(1, len(latencies)):
            if latencies[i] - latencies[i - 1] > gap_threshold_samples:
                trial_groups.append(
                    trial_group(
                        start_sample=current_group_start,
                        end_sample=current_group_end,
                        start_idx=current_start_idx,
                        end_idx=i - 1,
                    )
                )
                current_group_start = latencies[i]
                current_start_idx = i
            current_group_end = latencies[i]

        trial_groups.append(
            trial_group(
                start_sample=current_group_start,
                end_sample=current_group_end,
                start_idx=current_start_idx,
                end_idx=len(latencies) - 1,
            )
        )

        return trial_groups

    def _extract_trials(
        eeg_data: np.ndarray,
        latencies_ms: list[int],
        trial_groups: list[trial_group],
        adapt_trials: int = ADAPT_TRIALS,
        trial_time_frame_sec: int = WINDOW_TIME_FRAME,
        sampling_rate: int = SAMPLING_RATE,
    ) -> list[trial_info]:
        all_trials = []
        samples_per_trial = sampling_rate * trial_time_frame_sec

        for i, tg in enumerate(trial_groups):
            start_sample = tg.start_sample
            epoch = eeg_data[:, start_sample : start_sample + samples_per_trial]

            if epoch.shape[1] != samples_per_trial:
                continue

            dins_ms = latencies_ms[tg.start_idx : tg.end_idx + 1]
            n_dins = len(dins_ms)
            true_freq = 0.0
            closest = 0.0

            if n_dins > 1:
                intervals = [
                    dins_ms[j] - dins_ms[j - 1] for j in range(1, len(dins_ms))
                ]
                true_freq = (1000.0 / np.mean(intervals)) / 2.0
                closest = min(EXPECTED_FREQS, key=lambda f: abs(f - true_freq))

            trial_type = TrialType.ADAPT if i < adapt_trials else TrialType.TEST

            trial_record = trial_info(
                epoch=epoch,
                trial=i,
                true_freq=round(true_freq, 2),
                closest_freq=closest,
                n_dins=n_dins,
                type=trial_type,
            )

            all_trials.append(trial_record)

        return all_trials

    def get_all_trials(self, filename: str) -> list[trial_info]:
        eeg_data, latencies_ms, latencies = self._load_data(filename)
        trial_groups = self._group_din_markers_into_trials(latencies, 250)
        all_trials = self._extract_trials(eeg_data, latencies_ms, trial_groups)

        return all_trials


class CSVDataReader(DataReader):
    def _load_data(self, filename):
        return super()._load_data(filename)

    def get_all_trials(self, filename):
        return super().get_all_trials(filename)
