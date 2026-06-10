import numpy as np
import matplotlib.pyplot as plt
import mne


def load_raw_data(
    filename: str, l_freq: float = 4.0, h_freq: float = 45.0
) -> mne.io.Raw:
    try:
        raw = mne.io.read_raw_fif(filename, preload=True)
        raw = raw.load_data()
        raw = raw.pick_types(eeg=True, stim=False, eog=False, exclude="bads")
        raw.apply_function(lambda x: x * 10**-6)

        raw.filter(l_freq=l_freq, h_freq=h_freq)
        raw.notch_filter(freqs=50)
        return raw
    except FileNotFoundError:
        print(f"Nie można znaleźć pliku '{filename}'.")
        return None

def load_data(
    filename: str,
    target_marker_freqs: list[float],
    l_freq: float = 4.0,
    h_freq: float = 45.0,
    window_time_frame: int = 5,
) -> dict[np.ndarray] | None:
    raw = load_raw_data(filename, l_freq=l_freq, h_freq=h_freq)
    results = {}
    if raw is not None:
        events, event_dict = mne.events_from_annotations(raw)
        print("Dostępne markery w nagraniu:", event_dict)

        for target_marker_freq in target_marker_freqs:
            target_event_id = None
            for marker_name, marker_id in event_dict.items():
                if f"TARGET_{target_marker_freq}" in marker_name:
                    target_event_id = marker_id
                    print(f"Wybrano marker: {marker_name} (ID: {marker_id})")
                    break

            if target_event_id is not None:
                epochs = mne.Epochs(
                    raw,
                    events,
                    event_id=target_event_id,
                    tmin=0.0,
                    tmax=window_time_frame,
                    baseline=None,
                    preload=True,
                )

                target_epoch_data = epochs.get_data()[0]
                print(f"Wyizolowano epoch o wymiarach: {target_epoch_data.shape}")
                results[target_marker_freq] = target_epoch_data
            else:
                print(
                    f"Nie odnaleziono markera dla bodźca: {target_marker_freq} Hz w pliku!"
                )
                results[target_marker_freq] = raw.get_data()
    else:
        return None

    return results
