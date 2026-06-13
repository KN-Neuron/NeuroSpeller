import math
import time
import pygame

class SSVEPStimulus:
    def __init__(self, x, y, size, freq, refresh_rate=60, label=""):
        self.rect = pygame.Rect(x, y, size, size)
        self.freq = freq
        self.refresh_rate = refresh_rate
        self.start_time = time.perf_counter()
        
        self.frame_count = 0
        self.phase = 0.0
        
        # Kolory
        self.current_color = (0, 0, 0) 
        self.text_color = (255, 255, 255) 
        
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', int(40), bold=True)
        
        self.rendered_text = []
        self._label = ""
        self.set_label(label)

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, new_label):
        self.set_label(new_label)

    def set_label(self, label):
        self._label = label
        self.rendered_text = []
        
        if not label:
            return
            
        # Margines wewnętrzny 
        padding_percent = 0.05
        target_width = int(self.rect.width * (1 - padding_percent * 2))
        
        # --- Algorytm zawijania tekstu ---
        explicit_segments = label.split('\n')
        final_lines = []
        line_height = self.font.get_linesize()
        
        for segment in explicit_segments:
            words = segment.split(' ')
            if not words or (len(words) == 1 and words[0] == ''):
                final_lines.append("") 
                continue

            current_line_words = []
            for word in words:
                test_line_str = ' '.join(current_line_words + [word])
                width, height = self.font.size(test_line_str)
                
                if width <= target_width:
                    current_line_words.append(word)
                else:
                    final_lines.append(' '.join(current_line_words))
                    current_line_words = [word]
            
            final_lines.append(' '.join(current_line_words))
            
        # --- Pre-renderowanie i wyśrodkowanie ---
        total_text_height = len(final_lines) * line_height
        start_y = self.rect.centery - (total_text_height // 2)
        
        for i, line_str in enumerate(final_lines):
            if not line_str: continue 
            
            line_surf = self.font.render(line_str, True, self.text_color)
            line_rect = line_surf.get_rect(centerx=self.rect.centerx)
            line_rect.y = start_y + i * line_height
            
            self.rendered_text.append((line_surf, line_rect))

    def update(self):
        if self.freq <= 0:
            self.current_color = (127, 0, 0)
            return

        self.phase += self.freq / self.refresh_rate
        while self.phase >= 1.0:
            self.phase -= 1.0
            
        if self.phase < 0.5:
            self.current_color = (255, 255, 255)
        else:
            self.current_color = (0, 0, 0)

    def draw(self, surface):
        # Renderowanie boxa
        pygame.draw.rect(surface, self.current_color, self.rect)
        
        # Renderowanie zbuforowanych liter
        for line_surf, line_rect in self.rendered_text:
            surface.blit(line_surf, line_rect)