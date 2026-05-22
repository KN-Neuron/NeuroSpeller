import pygame
import sys
import gc
from concurrent.futures import ThreadPoolExecutor

from src.config.app_config import *

from src.ui.grid import SpellerGrid
from src.ui.menu import draw_menu

from src.headset.streamer import Streamer
from src.pipeline.bci_engine import BCIEngine
from src.pipeline.predictor import CCAPredictor
from src.pipeline.preprocessor import EEGPreprocessor
from src.config.bci_config import (
    TARGET_CHANNELS,
    SG_WINDOW,
    SG_POLYORDER,
    SAMPLING_RATE,
    FREQS,
    WINDOW_TIME_FRAME,
    TRIAL_DURATION_MS,
    REST_DURATION_MS,
    SAMPLES_PER_WINDOW
)

# 1. PyGame setup
pygame.init()
streamer = Streamer(device_name="BA MIDI 072", simulate=False, window_seconds=WINDOW_TIME_FRAME)
preprocessor = EEGPreprocessor(TARGET_CHANNELS, SG_WINDOW, SG_POLYORDER)
predictor = CCAPredictor(FREQS, SAMPLING_RATE, SAMPLES_PER_WINDOW, 0.3)
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

prediction_executor = ThreadPoolExecutor(max_workers=1)
prediction_future = None

# Przechowuje wpisane słowo
typed_text = ""
# Obecny "folder" w menu
current_tree_node = "root"
# Historia, żeby przycisk BACK działał
node_history = []

# Kalibracja offline
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

                streamer.clear_session()
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

                if calib_idx < len(grid.stimuli):
                    # Bierzemy kolejny kafelek z ekranu (0..5)
                    target_stimulus = grid.stimuli[calib_idx]
                    current_target_freq = target_stimulus.freq
                    clean_label = target_stimulus.label.replace('\n', ' ')
                    streamer.send_marker(f"TARGET_{current_target_freq}_{clean_label}")
                    print(f"[OFFLINE] Kafelek {calib_idx + 1}/6: '{clean_label}' @ {current_target_freq} Hz")
                    phase_start_time = current_time
                else:
                    # Przeszliśmy po wszystkich 6 kafelkach — koniec fazy
                    streamer.send_marker("STOP-PHASE-OFFLINE")
                    current_target_freq = None
                    print("[OFFLINE] Kalibracja zakończona. Zapisuję dane do pliku FIF...")
                    streamer.save_to_file("offline_calibration.fif")
                    gc.enable()
                    state = "MENU"
        else:
            # Koniec czasu patrzenia na kafelek
            if elapsed_time > TRIAL_DURATION_MS:
                # Zaznacz kafelek na zielono (feedback wizualny)
                if calib_idx < len(grid.stimuli):
                    grid.stimuli[calib_idx].current_color = (0, 255, 0)

                is_resting = True
                current_target_freq = None
                phase_start_time = current_time
                calib_idx += 1

        # --- RYSOWANIE KAFELKÓW I INTERFEJSU ---
        grid.update()
        grid.draw(screen)

        # Ramka na wybranym kafelku
        if not is_resting and calib_idx < len(grid.stimuli):
            pygame.draw.rect(screen, (255, 215, 0), grid.stimuli[calib_idx].rect, 10)

        # Pasek informacyjny u góry
        pygame.draw.rect(screen, COLOR_GRAY, (0, 0, WIDTH, 70))
        font_inst = pygame.font.SysFont("Arial", 28, bold=True)

        if is_resting:
            if calib_idx < len(grid.stimuli):
                txt = font_inst.render(f"PRZERWA. Przygotuj się na kafelek {calib_idx + 1}/6...", True, (150, 150, 150))
            else:
                txt = font_inst.render("Kalibracja zakończona!", True, (0, 255, 0))
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 20))
        else:
            txt = font_inst.render(f"SKUP WZROK NA ZAZNACZONYM KAFELKU ({calib_idx + 1}/6)", True, (255, 215, 0))
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

        if current_time - last_predict_time > 3000 and prediction_future is None:
            prediction_future = prediction_executor.submit(bci_engine.predict)

        if prediction_future is not None and prediction_future.done():
            predicted_freq = prediction_future.result()
            prediction_future = None
            last_predict_time = current_time

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
prediction_executor.shutdown(wait=False)
pygame.quit()
sys.exit()
