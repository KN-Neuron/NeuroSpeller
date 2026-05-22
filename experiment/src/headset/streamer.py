import threading

import mne
import numpy as np
from brainaccess import core
from brainaccess.core.eeg_manager import EEGManager
import brainaccess.core.eeg_channel as eeg_channel
from brainaccess.core.gain_mode import GainMode
from ..config.bci_config import SAMPLING_RATE
from typing import Any


class Streamer:
    def __init__(
        self,
        device_name: str = "BA MIDI 072",
        simulate: bool = True,
        window_seconds: float = 2.0,
    ) -> None:
        self.simulate: bool = simulate
        self.device_name: str = device_name
        self.connected: bool = False
        self.sampling_rate: int = SAMPLING_RATE

        self.num_channels: int = 16
        self.max_samples: int = int(window_seconds * self.sampling_rate)
        self.buffer: np.ndarray = np.zeros((self.num_channels, self.max_samples))
        self._mutex: threading.Lock = threading.Lock()
        self.manager: EEGManager = EEGManager()
        self.all_data_session: list[np.ndarray] = []
        self.markers: list[tuple[float, str]] = []  # (timestamp_sec, label)
        self._sample_counter: int = 0  # licznik próbek do obliczania czasu markerów

    def _on_chunk_received(self, chunk: Any, chunk_size: int) -> None:
        data: np.ndarray = np.array(chunk)
        eeg_data: np.ndarray = data[: self.num_channels, :]
        self.all_data_session.append(eeg_data)
        self._sample_counter += chunk_size

        with self._mutex:
            self.buffer = np.roll(self.buffer, -chunk_size, axis=1)
            self.buffer[:, -chunk_size:] = eeg_data

    def get_current_window(self) -> np.ndarray:
        with self._mutex:
            return self.buffer.copy()

    def start(self) -> None:
        print("Odpalono start")

        if self.simulate:
            self.connected = True
            print("[Streamer] Tryb symulacji włączony.")
            return

        def _connect() -> None:
            try:
                core.init()
                self.manager.connect(self.device_name)

                # Pobierz liczbę kanałów z urządzenia
                features = self.manager.get_device_features()
                eeg_ch_count: int = features.electrode_count()
                print(f"[Streamer] Kanały EEG: {eeg_ch_count}")

                # Włącz kanały EEG
                for i in range(eeg_ch_count):
                    self.manager.set_channel_enabled(
                        eeg_channel.ELECTRODE_MEASUREMENT + i, True
                    )
                    self.manager.set_channel_gain(
                        eeg_channel.ELECTRODE_MEASUREMENT + i, GainMode.X8
                    )

                # Bias na ostatnim kanale
                self.manager.set_channel_bias(
                    eeg_channel.ELECTRODE_MEASUREMENT + (eeg_ch_count - 1), True
                )

                # Callback i load_config PRZED start_stream
                self.manager.set_callback_chunk(self._on_chunk_received)
                self.manager.load_config()
                self.manager.start_stream()

                self.connected = True
                print(f"[Streamer] Połączono z {self.device_name}!")
            except Exception as e:
                print(f"[Streamer] Błąd połączenia: {e}")
                self.connected = False

        t: threading.Thread = threading.Thread(target=_connect)
        t.start()
        t.join()

    def stop(self) -> None:
        if self.simulate or not self.connected or self.manager is None:
            return
        try:
            if self.manager.is_streaming():
                self.manager.stop_stream()
            self.manager.disconnect()
            core.close()
        except Exception as e:
            print(f"[Streamer] Błąd przy zatrzymywaniu: {e}")

    def send_marker(self, label) -> None:
        # Zawsze logujemy marker z aktualnym czasem (w sekundach)
        timestamp_sec = self._sample_counter / self.sampling_rate
        self.markers.append((timestamp_sec, label))
        print(f"[Marker] t={timestamp_sec:.3f}s: {label}")

        # Dodatkowo wysyłamy do urządzenia jeśli jest podłączone
        if not self.simulate and self.connected and self.manager:
            try:
                self.manager.annotate(label)
            except Exception as e:
                print(f"[Streamer] Błąd markera: {e}")

    def clear_session(self) -> None:
        """Czyści dane sesji przed nowym nagraniem."""
        self.all_data_session.clear()
        self.markers.clear()
        self._sample_counter = 0
        print("[Streamer] Sesja wyczyszczona.")

    def generate_mock_data(self, target_freq) -> None:
        if self.simulate:
            # 1. Zapewnienie ciągłości czasu (fazy fali), żeby sinusoida nie "skakała"
            if not hasattr(self, "mock_time"):
                self.mock_time = 0.0

            # 2. Dostosowanie do 60 FPS Pygame.
            # Jeśli SAMPLING_RATE = 250, to 250/60 = ~4 próbki na klatkę.
            chunk_samples = max(1, int(self.sampling_rate / 60))

            t = np.linspace(
                self.mock_time,
                self.mock_time + chunk_samples / self.sampling_rate,
                chunk_samples,
                endpoint=False,
            )
            self.mock_time += chunk_samples / self.sampling_rate

            # 3. Generujemy tło (szum) na wszystkie 16 kanałów
            noise = np.random.normal(0, 2.0, (self.num_channels, chunk_samples))
            chunk = noise

            # 4. Czysty sygnał o zadanej częstotliwości (np. 10 Hz)
            signal = 15.0 * np.sin(2 * np.pi * target_freq * t)

            # 5. WSTRZYKNIĘCIE do tych samych kanałów, które czyta bci_engine.py
            target_channels = [1, 6, 11]
            for ch in target_channels:
                chunk[ch, :] += signal

            self._on_chunk_received(chunk, chunk_samples)

    def save_to_file(self, filename="badanie_eeg_raw.fif"):
        if not self.all_data_session:
            print("[Streamer] Brak danych do zapisania.")
            return

        data = np.concatenate(self.all_data_session, axis=1)
        ch_names = [f"CH_{i}" for i in range(self.num_channels)]
        info = mne.create_info(
            ch_names=ch_names,
            sfreq=self.sampling_rate,
            ch_types='eeg'
        )
        raw = mne.io.RawArray(data, info)

        # Dodaj markery jako MNE Annotations do pliku FIF
        if self.markers:
            max_time = raw.times[-1]
            onsets = [min(m[0], max_time) for m in self.markers]
            descriptions = [m[1] for m in self.markers]
            durations = [0.0] * len(self.markers)
            annotations = mne.Annotations(
                onset=onsets,
                duration=durations,
                description=descriptions
            )
            raw.set_annotations(annotations)
            print(f"[Streamer] Dodano {len(self.markers)} markerów do pliku.")

        raw.save(filename, overwrite=True)
        print(f"[Streamer] Dane zapisane do {filename}. Shape: {data.shape}")