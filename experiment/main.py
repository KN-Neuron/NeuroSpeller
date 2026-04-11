import pygame
import sys
import gc

from config import *
from Speller import SSVEPStimulus, SpellerGrid
from Speller import menu

from experiment.eeg_headset.eeg_streamer import EEGStreamer
from experiment.eeg_headset.bci_engine import BCIEngine

# 1. PyGame setup
pygame.init()
streamer = EEGStreamer(device_name="BA MIDI 072", simulate=False)
bci_engine = BCIEngine(streamer=streamer, threshold=1.5)
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

            if event.key == pygame.K_2:
                gc.disable()

                state = "ONLINE"
                print("Startujemy Speller...")

                streamer.send_marker("START-PHASE-ONLINE")


    screen.fill((0, 0, 0))

    if state == "MENU":
        menu.draw_menu(screen, is_connected=streamer.connected)

    if state == "OFFLINE":
        grid.update()
        grid.draw(screen)

    if state == "ONLINE":
        grid.update()
        grid.draw(screen)

        # RYSOWANIE PASKA TEKSTU NA GÓRZE EKRANU
        pygame.draw.rect(screen, COLOR_GRAY, (50, 20, WIDTH - 100, 70))
        font_speller = pygame.font.SysFont('Arial', 48, bold=True)
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