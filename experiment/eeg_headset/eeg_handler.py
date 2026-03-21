import numpy as np
import brainaccess.core as ba_core
from brainaccess.core.eeg_manager import EEGManager

class BrainAccessBackend:
    def __init__(self, device_name="BA-MIDI", simulate=True):
        self.simulate = simulate
        self.device_name = device_name
        self.data_buffer = []
        self.connected = False

        if not self.simulate:
            ba_core.init()
            self.eeg = EEGManager()
            self.eeg.set_callback_chunk(self._on_chunk_received)

    def _on_chunk_received(self, chunk):
        self.data_buffer.append(chunk)

    def start(self):
        if self.simulate:
            print("[Backend] Tryb testowy: Pomijam łączenie z czepkiem.")
            self.connected = False
            return

        try:
            self.eeg.connect(bt_device_name=self.device_name)
            self.eeg.start_stream()
            self.connected = True
            print(f"[Backend] Połączono z {self.device_name}.")
        except Exception as e:
            print(f"[Backend] Błąd połączenia: {e}")
            self.connected = False

    def send_marker(self, label):
        if self.simulate or not self.connected:
            print(f"[Backend Mock] Wysłano marker: {label}")
            return

        try:
            if self.eeg.is_connected():
                self.eeg.annotate(label)
        except Exception as e:
            print(e)

    def stop(self):
        if self.simulate or not self.connected:
            print("[Backend Mock] Koniec sesji.")
            return

        try:
            if self.eeg.is_streaming():
                self.eeg.stop_stream()
            if self.eeg.is_connected():
                self.eeg.disconnect()

            if self.data_buffer:
                np.save("eeg_session_data.npy", np.array(self.data_buffer, dtype=object))
        except Exception as e:
            print(e)

    def is_device_connected(self):
        return self.connected