from collections import defaultdict
from data_classes import trial_info, TrialType


def group_trials_by_frequency(
    trials: list[trial_info],
) -> dict[float, list[trial_info]]:
    freq_dict = defaultdict(list)
    for t in trials:
        if t.closest_freq > 0:
            freq_dict[t.closest_freq].append(t)
    return freq_dict


def get_trials_by_type(
    trials: list[trial_info], trial_type: TrialType
) -> list[trial_info]:
    return [t for t in trials if t.type == trial_type]
