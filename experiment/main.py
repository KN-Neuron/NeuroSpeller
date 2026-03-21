import pygame
import sys
import gc

from config import *
from Speller import SSVEPStimulus, SpellerGrid
from Speller import menu

from experiment.eeg_headset.egg_handler import BrainAccessBackend

# 1. PyGame setup
pygame.init()
eeg_handler = BrainAccessBackend(device_name="BA-MIDI")

# 2. Ustawienia ekranu
screen = pygame.display.set_mode((WIDTH, HEIGHT), vsync=1)
pygame.display.set_caption("SSVEP Speller Experiment")

# 3. Zegar
clock = pygame.time.Clock()

# 4. Tworzymy obiekt
grid = SpellerGrid((WIDTH, HEIGHT), FREQS, ALPHABET_TREE["root"])

state = "MENU"

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

                eeg_handler.start()
                eeg_handler.send_marker("START-PHASE-OFFLINE")

            if event.key == pygame.K_2:
                gc.disable()

                state = "ONLINE"
                print("Startujemy Speller...")

                eeg_handler.start()
                eeg_handler.send_marker("START-PHASE-ONLINE")
    
    
    screen.fill((0, 0, 0))

    if state == "MENU":
        try:
            is_connected = eeg_handler.eeg.is_connected()
        except Exception as e:
            print(e)
        finally:
            menu.draw_menu(screen, is_connected = False)

    if state == "OFFLINE":
        grid.update()
        grid.draw(screen)

    if state == "ONLINE":
        grid.update()
        grid.draw(screen)

    pygame.display.flip()

    clock.tick(60)

eeg_handler.stop()
pygame.quit()
sys.exit()