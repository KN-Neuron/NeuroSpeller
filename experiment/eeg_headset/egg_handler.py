import numpy as np
import brainaccess.core as ba_core
from brainaccess.core.eeg_manager import EEGManager


class BrainAccessBackend:
    def __init__(self, device_name="BA-MIDI"):
        ba_core.init()
        self.eeg = EEGManager()
        self.device_name = device_name
        self.data_buffer = []
        self.eeg.set_callback_chunk(self._on_chunk_received)

    def _on_chunk_received(self, chunk):
        self.data_buffer.append(chunk)

    def start(self):
        try:
            self.eeg.connect(bt_device_name=self.device_name)
            self.eeg.start_stream()
            print(f"[Backend] Połączono z {self.device_name}. Akwizycja w tle.")
        except Exception as e:
            print(f"[Backend] Błąd połączenia: {e}")

    def send_marker(self, label):
        try:
            if self.eeg.is_connected():
                self.eeg.annotate(label)
                print(f"[Backend] Zapisano anotację: {label}")
        except Exception:
            pass

    def stop(self):
        try:
            if self.eeg.is_streaming():
                self.eeg.stop_stream()
            if self.eeg.is_connected():
                self.eeg.disconnect()

            # Zapisanie zebranych danych po zamknięciu aplikacji
            if self.data_buffer:
                np.save("eeg_session_data.npy", np.array(self.data_buffer, dtype=object))
                print(f"[Backend] Zapisano {len(self.data_buffer)} paczek do pliku eeg_session_data.npy")
        except Exception as e:
            print(f"[Backend] Błąd przy zamykaniu: {e}")