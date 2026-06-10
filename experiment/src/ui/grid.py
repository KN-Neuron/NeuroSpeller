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

        # Stały rozmiar kafelka
        size = 200

        # Odstępy między kafelkami (niezależne od rozmiaru)
        margin_x = 350
        margin_y = 300

        # 2. ------------------------------------ Ustawianie siatki  ------------------------------------
        
        # Całkowita szerokość i wysokość całego boxa gridu
        total_grid_width = (cols * size) + ((cols - 1) * margin_x)
        total_grid_height = (rows * size) + ((rows - 1) * margin_y)
        
        start_x = (self.width - total_grid_width) // 2
        start_y = (self.height - total_grid_height) // 2
        
        # 5. ------------------------------------ Konstrukcja kafelków ------------------------------------
        for i in range(len(labels)):
            col = i % cols
            row = i // cols
            
            # Nowa pozycja z uwzględnieniem start_x i start_y
            x = start_x + col * (size + margin_x)
            y = start_y + row * (size + margin_y)
            
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