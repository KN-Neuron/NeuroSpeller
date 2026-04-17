# KPP — Kompleksowe Podsumowanie Projektu

## 1. Informacje ogólne
- **Nazwa projektu:** NeuroSpeller
- **Zespół:**
  - Kacper Daniel - Lider Projektu
  - Aleksander Czop - Frontend Developer
  - Michał Szandarowski - Data Science
  - Michał Śliwa - Backend Developer
  - Ewa Śmigaj - Frontend Developer
- **Okres realizacji:** Od grudnia 2025 (w toku, faza implementacji technicznej)
- **Repozytorium:** https://github.com/KN-Neuron/NeuroSpeller
- **Wersja dokumentu:** 1.0 (Stan na 17.04.2026)

---

## 2. Cel projektu

### 2.1 Problem
Osoby z poważnymi dysfunkcjami motorycznymi mają trudności z tradycyjnymi formami komunikacji. Projekt rozwiązuje ten problem poprzez stworzenie interfejsu mózg-komputer, który pozwala na wpisywanie tekstu bez użycia mięśni, wykorzystując jedynie aktywność bioelektryczną mózgu.

### 2.2 Motywacja
Główną motywacją jest edukacja nowych członków koła poprzez praktyczne przejście przez pełen cykl projektowy: od przeglądu literatury, przez planowanie eksperymentu, aż po budowę działającej aplikacji. A przy okazji stworzenie czegoś ciekawego, co rozwiązuje rzeczywisty problem.

---

## 3. Przegląd rozwiązania

### 3.1 Opis ogólny
System to speller BCI oparty na paradygmacie SSVEP (Steady-State Visual Evoked Potentials). Użytkownik patrzy na kafelki migające z różną częstotliwością, co wywołuje w płacie potylicznym sygnał o odpowiadającej częstotliwości. System rozpoznaje, na który element patrzy użytkownik, i na tej podstawie nawiguje po interfejsie.

### 3.2 Architektura
Projekt opiera się na przepływie danych w czasie rzeczywistym z API BrainAccess.

[Czepek EEG (BrainAccess)] → [API (Data Stream/.fif)] → [Backend (Python Processing)] → [Frontend (UI Stimuli)]

### 3.3 Główne komponenty
- Moduł Akwizycji - odpowiada za połączenie z czepkiem i czytanie danych real-time i/lub w formacie .fif przez dedykowane API
- Silnik Procesowania do klasyfikacji sygnału w trybie online
- GUI: Aplikacja z 6 migającymi kafelkami, realizująca hierarchiczny wybór znaków (np. START -> Grupa liter -> Konkretna litera)

---

## 4. Technologie i decyzje projektowe

### 4.1 Stack technologiczny
- Język: Python
- Frontend: Pygame
- Backend: BrainAccess API
- Przetwarzanie danych: MNE

### 4.2 Kluczowe decyzje
- Decyzja: Wybór SSVEP
  - Dlaczego: Ciekawe
  - Alternatywy: P300, Motor Imagery 
- Decyzja: Hierarchiczna struktura wyboru (START -> Grupa -> Znak)
  - Dlaczego: Pozwala na obsługę pełnego alfabetu przy użyciu tylko 6 kafelków, co zwiększa stabilność klasyfikacji SSVEP przy mniejszej liczbie częstotliwości
  - Alternatywy: Wyświetlanie od razu całej klawiatury i traktowanie każdego klawisza jako odrębnej częstotliwości

---

## 5. Implementacja

### 5.1 Struktura projektu
```
/data
  /src
/experiment 
  /Speller
  /eeg_headset
/docs
```

### 5.2 Kluczowe elementy
- Faza Offline: Służy do zebrania danych kalibracyjnych i testowania filtrów na nagranych sygnałach
- Faza Online: Procesowanie danych w czasie rzeczywistym w celu sterowania spellerem
- Przycisk START: Mechanizm aktywujący kafelki dopiero po skupieniu wzroku na konkretnym punkcie, co zapobiega przypadkowym wpisom.

### 5.3 Nietrywialne rozwiązania
Zastosowanie hierarchicznego systemu wpisywania (np. START -> "ABCDEFGHIJ" -> "ABCDE" -> "B") pozwala na zachowanie wysokiej dokładności przy ograniczonej liczbie stymulatorów, co jest kluczowe dla początkujących użytkowników i prostego sprzętu EEG.

---

## 6. Jak uruchomić projekt!

### 6.1 Wymagania
- np. Node.js 18
- .NET 8
- Docker

### 6.2 Instalacja
```bash
git clone ...
cd project
npm install
```

### 6.3 Uruchomienie
```bash
npm run dev
```

### 6.4 First steps
...

---

## 7. Wyniki

### 7.1 Co działa

- Feature 1
- Feature 2

### 7.2 Demo
link / opis / screenshot

### 7.3 Metryki (ważne dla projektów z ML)
- wydajność
- dokładność
- inne

---

## 8. Problemy i wyzwania

```
Problem: ...

Opis: ...

Rozwiązanie: ...
```

---

## 9. Wnioski

### 9.1 Czego się nauczyliśmy
...

### 9.2 Co zrobilibyśmy inaczej
...

---

## 10. Możliwe rozwinięcia

- Pomysł 1
- Pomysł 2

---

## 11. Reproducibility Checklist

**Sprawdź przed oddaniem:**

- [ ] Projekt da się uruchomić na czystym środowisku
- [ ] Instrukcja uruchomienia działa krok po kroku
- [ ] Wszystkie zależności są opisane
- [ ] Demo działa zgodnie z opisem

---

## 12. Załączniki
diagramy / linki / dodatkowe materiały

---

## 13. Status projektu

W trakcie