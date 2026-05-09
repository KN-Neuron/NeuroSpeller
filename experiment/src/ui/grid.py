import pygame
from src.ui.stimulus import SSVEPStimulus

class SpellerGrid:
    def __init__(self, screen_res, frequencies, labels):
        self.width, self.height = screen_res
        self.stimuli = []
        
        # 1. ------------------------------------ Struktura Obiektu ------------------------------------
    
        # (3 kolumny, 2 rzędy = 6 kafelków)
        cols = 3
        rows = 2

        # Odstęp między kafelkami
        margin = 80  

        # 2. ------------------------------------ Symetryczne ustawianie siatki  ------------------------------------
        
        
        # 2. Obliczamy maksymalny możliwy rozmiar kafelka, który wejdzie na ekran
        available_w = self.width - (cols + 1) * margin
        available_h = self.height - (rows + 1) * margin
        
        tile_w = available_w // cols
        tile_h = available_h // rows
        
        # Rozmiar boku kwadratu (wybieramy mniejszy, by zachować proporcje 1:1)
        size = min(tile_w, tile_h)
        
        # Całkowita szerokość i wysokość całego boxa gridu
        total_grid_width = (cols * size) + ((cols - 1) * margin)
        total_grid_height = (rows * size) + ((rows - 1) * margin)
        

        start_x = (self.width - total_grid_width) // 2
        start_y = (self.height - total_grid_height) // 2
        
        # 5. ------------------------------------ Konstrukcja kafelków z uwzględnieniem offsetu ------------------------------------
        for i in range(len(labels)):
            col = i % cols
            row = i // cols
            
            # Nowa pozycja z uwzględnieniem start_x i start_y
            x = start_x + col * (size + margin)
            y = start_y + row * (size + margin)
            
            s = SSVEPStimulus(x, y, size, frequencies[i], label=labels[i])
            self.stimuli.append(s)


    def update(self):
        for s in self.stimuli:
            s.update()


    def draw(self, surface):
        for s in self.stimuli:
            s.draw(surface)


    def set_labels(self, new_labels):
        for i, label in enumerate(new_labels):
            if i < len(self.stimuli):
                self.stimuli[i].label = label