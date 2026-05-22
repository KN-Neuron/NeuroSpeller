import sys
import os
import mne

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.join(script_dir, "..", "..")  # scripts -> src -> experiment
default_fif = os.path.join(project_dir, "offline_calibration.fif")

raw = mne.io.read_raw_fif(default_fif, preload=True)

print("=" * 60)
print(f"PLIK: {default_fif}")
print(f"Kanały: {raw.info['nchan']}")
print(f"Sampling rate: {raw.info['sfreq']} Hz")
print(f"Czas trwania: {raw.times[-1]:.2f} s")
print(f"Próbki: {raw.n_times}")
print(f"Nazwy kanałów: {raw.ch_names}")
print("=" * 60)

# --- 3. Markery (Annotations) ---
annotations = raw.annotations
if len(annotations) > 0:
    print(f"\nMARKERY ({len(annotations)}):")
    print("-" * 60)
    for ann in annotations:
        print(f"  t={ann['onset']:8.3f}s  |  {ann['description']}")
    print("-" * 60)
else:
    print("\nBrak markerów w pliku.")

# --- 4. Podgląd danych (pierwsze 10 próbek, 3 kanały) ---
data = raw.get_data()
print(f"\nShape danych: {data.shape}  (kanały x próbki)")
print(f"Pierwsze 10 próbek z CH_0: {data[0, :10]}")
print(f"Pierwsze 10 próbek z CH_1: {data[1, :10]}")

# --- 5. Opcjonalnie: wykres ---
try:
    raw.plot(duration=10, n_channels=6, scalings="auto", title=default_fif)
    import matplotlib.pyplot as plt
    plt.show()
except Exception:
    print("\n(Wykres niedostępny — brak GUI lub matplotlib)")
