import threading
import numpy as np
from brainaccess import core
from brainaccess.core.eeg_manager import EEGManager
import brainaccess.core.eeg_channel as eeg_channel
from brainaccess.core.gain_mode import GainMode
from data.src.consts import SAMPLING_RATE


class EEGStreamer:
    def __init__(self, device_name="BA MIDI 072", simulate=True, window_seconds=2.0):
        self.simulate = simulate
        self.device_name = device_name
        self.connected = False
        self.sampling_rate = SAMPLING_RATE

        self.num_channels = 16
        self.max_samples = int(window_seconds * self.sampling_rate)
        self.buffer = np.zeros((self.num_channels, self.max_samples))
        self._mutex = threading.Lock()
        self.mgr = None
        self.all_data_session = []

    def _on_chunk_received(self, chunk, chunk_size):
        data = np.array(chunk)
        eeg_data = data[:self.num_channels, :]
        self.all_data_session.append(eeg_data)

        with self._mutex:
            self.buffer = np.roll(self.buffer, -chunk_size, axis=1)
            self.buffer[:, -chunk_size:] = eeg_data

    def get_current_window(self):
        with self._mutex:
            return self.buffer.copy()

    def start(self):
        print("Odpalono start")

        if self.simulate:
            self.connected = True
            print("[Streamer] Tryb symulacji włączony.")
            return

        def _connect():
            try:
                core.init()
                self.mgr = EEGManager()
                self.mgr.connect(self.device_name)

                # Pobierz liczbę kanałów z urządzenia
                features = self.mgr.get_device_features()
                eeg_ch_count = features.electrode_count()
                print(f"[Streamer] Kanały EEG: {eeg_ch_count}")

                # Włącz kanały EEG
                for i in range(eeg_ch_count):
                    self.mgr.set_channel_enabled(
                        eeg_channel.ELECTRODE_MEASUREMENT + i, True
                    )
                    self.mgr.set_channel_gain(
                        eeg_channel.ELECTRODE_MEASUREMENT + i, GainMode.X8
                    )

                # Bias na ostatnim kanale
                self.mgr.set_channel_bias(
                    eeg_channel.ELECTRODE_MEASUREMENT + (eeg_ch_count - 1), True
                )

                # Callback i load_config PRZED start_stream
                self.mgr.set_callback_chunk(self._on_chunk_received)
                self.mgr.load_config()
                self.mgr.start_stream()

                self.connected = True
                print(f"[Streamer] Połączono z {self.device_name}!")
            except Exception as e:
                print(f"[Streamer] Błąd połączenia: {e}")
                self.connected = False

        t = threading.Thread(target=_connect)
        t.start()
        t.join()

    def stop(self):
        if self.simulate or not self.connected or self.mgr is None:
            return
        try:
            if self.mgr.is_streaming():
                self.mgr.stop_stream()
            self.mgr.disconnect()
            core.close()
        except Exception as e:
            print(f"[Streamer] Błąd przy zatrzymywaniu: {e}")

    def send_marker(self, label):
        if not self.simulate and self.connected and self.mgr:
            try:
                self.mgr.annotate(label)
            except Exception as e:
                print(f"[Streamer] Błąd markera: {e}")

    def generate_mock_data(self, target_freq):
        if self.simulate:
            # 1. Zapewnienie ciągłości czasu (fazy fali), żeby sinusoida nie "skakała"
            if not hasattr(self, 'mock_time'):
                self.mock_time = 0.0

            # 2. Dostosowanie do 60 FPS Pygame.
            # Jeśli SAMPLING_RATE = 250, to 250/60 = ~4 próbki na klatkę.
            chunk_samples = max(1, int(self.sampling_rate / 60))

            t = np.linspace(self.mock_time, self.mock_time + chunk_samples/self.sampling_rate, chunk_samples, endpoint=False)
            self.mock_time += chunk_samples / self.sampling_rate

            # 3. Generujemy tło (szum) na wszystkie 16 kanałów
            noise = np.random.normal(0, 2.0, (self.num_channels, chunk_samples))
            chunk = noise

            # 4. Czysty sygnał o zadanej częstotliwości (np. 10 Hz)
            signal = 15.0 * np.sin(2 * np.pi * target_freq * t) # Zwiększyłem lekko amplitudę na 15.0

            # 5. WSTRZYKNIĘCIE do tych samych kanałów, które czyta bci_engine.py
            target_channels = [1, 6, 11]
            for ch in target_channels:
                chunk[ch, :] += signal

            self._on_chunk_received(chunk, chunk_samples)

    def save_to_file(self, filename="badanie_eeg.npy"):
        if not self.all_data_session:
            print("Brak danych do zapisu.")
            return
        full_array = np.concatenate(self.all_data_session, axis=1)
        np.save(filename, full_array)
        print(f"Dane zapisane do {filename}. Shape: {full_array.shape}")