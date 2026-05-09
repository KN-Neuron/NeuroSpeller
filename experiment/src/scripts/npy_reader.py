import numpy as np
import matplotlib.pyplot as plt

# Wczytanie danych[cite: 11]
dane = np.load("badanie_eeg.npy")

# Konfiguracja
SAMPLING_RATE = 250
KANAL = 1
CZAS_W_SEKUNDACH = 20

# Wycięcie danych
ilosc_probek = SAMPLING_RATE * CZAS_W_SEKUNDACH
sygnal = dane[KANAL, :ilosc_probek]

# Stworzenie osi czasu (X) w sekundach
czas = np.arange(ilosc_probek) / SAMPLING_RATE

# Rysowanie wykresu
plt.figure(figsize=(12, 4))
plt.plot(czas, sygnal, color='blue', linewidth=1)
plt.title(f"Zapis EEG - Kanał {KANAL} (Pierwsze {CZAS_W_SEKUNDACH} sekund)")
plt.xlabel("Czas (sekundy)")
plt.ylabel("Amplituda (mikrowolty)")
plt.grid(True)
plt.tight_layout()
plt.show()