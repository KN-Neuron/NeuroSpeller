import pygame
import sys
import gc

from experiment.src.config.app_config import *
from experiment.src.config.scenarios import SCENARIOS
from experiment.src.ui.grid import SpellerGrid
from experiment.src.ui.menu import draw_menu

from experiment.src.headset.streamer import Streamer
from experiment.src.pipeline.bci_engine import BCIEngine
from experiment.src.pipeline.predictor import CCAPredictor
from experiment.src.pipeline.preprocessor import EEGPreprocessor
from experiment.src.config.bci_config import (
    TARGET_CHANNELS,
    SG_WINDOW,
    SG_POLYORDER,
    SAMPLING_RATE,
    FREQS,
    WINDOW_TIME_FRAME,
    TRIAL_DURATION_MS,
    REST_DURATION_MS
)

# 1. PyGame setup
pygame.init()
streamer = Streamer(device_name="BA MIDI 072", simulate=True)
preprocessor = EEGPreprocessor(TARGET_CHANNELS, SG_WINDOW, SG_POLYORDER)
predictor = CCAPredictor(FREQS, SAMPLING_RATE, WINDOW_TIME_FRAME, 0.3)
bci_engine = BCIEngine(
    streamer=streamer, predictor=predictor, preprocessor=preprocessor
)
streamer.start()

# 2. Ustawienia ekranu
screen = pygame.display.set_mode((WIDTH, HEIGHT), vsync=1)
pygame.display.set_caption("SSVEP Speller Experiment")

# 3. Zegar
clock = pygame.time.Clock()

# 4. Tworzymy obiekt
grid = SpellerGrid((WIDTH, HEIGHT), FREQS, ALPHABET_TREE["root"])
state = "MENU"

last_predict_time = 0

# Przechowuje wpisane słowo
typed_text = ""
# Obecny "folder" w menu
current_tree_node = "root"
# Historia, żeby przycisk BACK działał
node_history = []

# Kalibracja offline
wybrany_scenariusz = SCENARIOS["WPISZ_A"]
calibration_sequence = wybrany_scenariusz
calib_idx = 0
current_target_freq = None
phase_start_time = 0
is_resting = True

running = True

while running:
    events = pygame.event.get()

    for event in events:
        gc.collect()

        if event.type == pygame.QUIT:
            running = False

        if state == "MENU" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                gc.disable()

                state = "OFFLINE"
                print("Startujemy fazę kalibracji...")

                streamer.send_marker("START-PHASE-OFFLINE")

                calib_idx = 0
                is_resting = True
                phase_start_time = pygame.time.get_ticks()

            if event.key == pygame.K_2:
                gc.disable()

                state = "ONLINE"
                print("Startujemy Speller...")

                streamer.send_marker("START-PHASE-ONLINE")

    screen.fill((0, 0, 0))

    if state == "MENU":
        draw_menu(screen, is_connected=streamer.connected)

    if state == "OFFLINE":
        if streamer.simulate:
            if not is_resting and current_target_freq is not None:
                streamer.generate_mock_data(target_freq=current_target_freq)
            else:
                streamer.generate_mock_data(target_freq=0.0)

        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - phase_start_time

        if is_resting:
            if elapsed_time > REST_DURATION_MS:
                is_resting = False

                if calib_idx < len(calibration_sequence):
                    # 1. Bierzemy dokładny tekst ze scenariusza
                    target_label = calibration_sequence[calib_idx]
                    current_target_freq = None

                    # 2. Przeszukujemy kafelki na ekranie
                    for stimulus in grid.stimuli:
                        if stimulus.label == target_label:
                            current_target_freq = stimulus.freq
                            break

                    # 3. Akcja jeśli znaleziono kafelek
                    if current_target_freq is not None:
                        # Usuwamy entery (\n) na potrzeby czytelnego markera w pliku
                        clean_label = target_label.replace('\n', ' ')
                        streamer.send_marker(f"TARGET_{current_target_freq}_{clean_label}")
                    else:
                        print(f"[BŁĄD] Brak kafelka o nazwie '{target_label}' na tym ekranie!")

                    phase_start_time = current_time
                else:
                    streamer.send_marker("STOP-PHASE-OFFLINE")
                    current_target_freq = None
                    state = "MENU"
        else:
            # --- ZMIANA: KONIEC CZASU = SYMULACJA KLIKNIĘCIA ---
            if elapsed_time > TRIAL_DURATION_MS:
                for stimulus in grid.stimuli:
                    if stimulus.freq == current_target_freq:
                        # 1. Zaznacz na zielono
                        stimulus.current_color = (0, 255, 0)
                        label = stimulus.label

                        # 2. Logika nawigacji (skopiowana z ONLINE)
                        if label == "MAIN":
                            current_tree_node = "root"
                            node_history.clear()
                            grid.set_labels(ALPHABET_TREE[current_tree_node])
                        elif label == "BACK":
                            if node_history:
                                current_tree_node = node_history.pop()
                            else:
                                current_tree_node = "root"
                            grid.set_labels(ALPHABET_TREE[current_tree_node])
                        elif label == "UNDO" or label == "Del":
                            typed_text = typed_text[:-1]
                        elif label == "Blank":
                            typed_text += " "
                        elif label in ALPHABET_TREE:
                            node_history.append(current_tree_node)
                            current_tree_node = label
                            grid.set_labels(ALPHABET_TREE[current_tree_node])
                        else:
                            if len(label) == 1:
                                typed_text += label
                                current_tree_node = "root"
                                node_history.clear()
                                grid.set_labels(ALPHABET_TREE[current_tree_node])
                        break

                is_resting = True
                current_target_freq = None
                phase_start_time = current_time
                calib_idx += 1

        # --- RYSOWANIE KAFELKÓW I INTERFEJSU ---
        grid.update()
        grid.draw(screen)  # Najpierw rysujemy kafelki

        # Następnie nakładamy ramkę na wierzch wybranego kafelka
        if not is_resting and current_target_freq is not None:
            for stimulus in grid.stimuli:
                if stimulus.freq == current_target_freq:
                    pygame.draw.rect(screen, (255, 215, 0), stimulus.rect, 10)

        # Rysowanie paska wpisanego tekstu w trybie OFFLINE (żeby widzieć efekt)
        pygame.draw.rect(screen, COLOR_GRAY, (50, 80, WIDTH - 100, 70))
        font_speller = pygame.font.SysFont("Arial", 48, bold=True)
        text_surf = font_speller.render(typed_text + "_", True, COLOR_WHITE)
        screen.blit(text_surf, (70, 90))

        # Pasek postępu u góry
        pygame.draw.rect(screen, COLOR_GRAY, (0, 0, WIDTH, 70))
        font_inst = pygame.font.SysFont("Arial", 28, bold=True)

        if is_resting:
            txt = font_inst.render(f"PRZERWA. Przygotuj się...", True, (150, 150, 150))
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 20))
        else:
            txt = font_inst.render("SKUP WZROK NA ZAZNACZONYM KAFELKU", True, (255, 215, 0))
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 5))
            progress_ratio = elapsed_time / TRIAL_DURATION_MS
            bar_width = int(400 * progress_ratio)
            pygame.draw.rect(screen, (50, 50, 50), (WIDTH // 2 - 200, 40, 400, 15))
            pygame.draw.rect(screen, (255, 215, 0), (WIDTH // 2 - 200, 40, bar_width, 15))

    if state == "ONLINE":
        grid.update()
        grid.draw(screen)

        # RYSOWANIE PASKA TEKSTU NA GÓRZE EKRANU
        pygame.draw.rect(screen, COLOR_GRAY, (50, 20, WIDTH - 100, 70))
        font_speller = pygame.font.SysFont("Arial", 48, bold=True)
        text_surf = font_speller.render(typed_text + "_", True, COLOR_WHITE)
        screen.blit(text_surf, (70, 30))

        # SYMULACJA I BCI
        if streamer.simulate:
            streamer.generate_mock_data(target_freq=10.0)

        current_time = pygame.time.get_ticks()

        if current_time - last_predict_time > 3000:
            predicted_freq = bci_engine.predict()

            if predicted_freq:
                for stimulus in grid.stimuli:
                    if stimulus.freq == predicted_freq:
                        label = stimulus.label
                        print(f"[SPELLER] Kliknięto: {label}")

                        # Zaznaczenie wizualne
                        stimulus.current_color = (0, 255, 0)

                        # --- LOGIKA DRZEWA ---
                        if label == "MAIN":
                            current_tree_node = "root"
                            node_history.clear()
                            grid.set_labels(ALPHABET_TREE[current_tree_node])

                        elif label == "BACK":
                            if node_history:
                                current_tree_node = node_history.pop()
                            else:
                                current_tree_node = "root"
                            grid.set_labels(ALPHABET_TREE[current_tree_node])

                        elif label == "UNDO" or label == "Del":
                            typed_text = typed_text[:-1]

                        elif label == "Blank":
                            typed_text += " "

                        elif label in ALPHABET_TREE:
                            node_history.append(current_tree_node)
                            current_tree_node = label
                            grid.set_labels(ALPHABET_TREE[current_tree_node])

                        else:
                            # TO JEST LITERA!
                            if len(label) == 1:
                                typed_text += label
                                current_tree_node = "root"
                                node_history.clear()
                                grid.set_labels(ALPHABET_TREE[current_tree_node])
                        break

            last_predict_time = current_time

    pygame.display.flip()

    clock.tick(60)

streamer.stop()
streamer.save_to_file()
pygame.quit()
sys.exit()
