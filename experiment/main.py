import pygame
import sys
import gc

from config import *
from Speller import SSVEPStimulus, SpellerGrid
from Speller import menu


# 1. PyGame setup
pygame.init()

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

            if event.key == pygame.K_2:
                gc.disable()

                state = "ONLINE"
                print("Startujemy Speller...")
    
    
    screen.fill((0, 0, 0))

    if state == "MENU":
        menu.draw_menu(screen) 

    if state == "OFFLINE":
        grid.update()
        grid.draw(screen)

    if state == "ONLINE":
        grid.update()
        grid.draw(screen)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()