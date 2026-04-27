import math
import pygame

class SSVEPStimulus:
    def __init__(self, x, y, size, freq, refresh_rate=60, label=""):
        self.rect = pygame.Rect(x, y, size, size)
        self.freq = freq
        self.refresh_rate = refresh_rate
        self.label = label
        self.frame_count = 0
        
        # Kolory
        self.current_color = (0, 0, 0) 
        self.text_color = (255, 255, 255) 
        
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', int(40), bold=True)

    def update(self):
        t = self.frame_count / self.refresh_rate
        
        sine_val = math.sin(2 * math.pi * self.freq * t)
        
        intensity = int(127.5 * (sine_val * 0.5 + 1.0))
        
        self.current_color = (intensity, 0, 0)
        
        self.frame_count += 1

    def draw(self, surface):
        # Renderowanie boxa
        pygame.draw.rect(surface, self.current_color, self.rect)
        
        # Renderowanie liter w boxie
        if self.label:
            # Margines wewnętrzny 
            padding_percent = 0.05
            target_width = int(self.rect.width * (1 - padding_percent * 2))
            
            # --- Algorytm zawijania tekstu ---
            
            explicit_segments = self.label.split('\n')
            final_lines = []
            
            line_height = self.font.get_linesize()
            
            # Przetwarzamy każdy segment
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
                
            # --- Renderowanie i wyśrodkowanie ---
            
            total_text_height = len(final_lines) * line_height
            
            start_y = self.rect.centery - (total_text_height // 2)
            
            # Renderujemy każdą linię po kolei
            for i, line_str in enumerate(final_lines):
                if not line_str: continue 
                
                line_surf = self.font.render(line_str, True, self.text_color)
                
                line_rect = line_surf.get_rect(centerx=self.rect.centerx)
                
                line_rect.y = start_y + i * line_height
                
                surface.blit(line_surf, line_rect)