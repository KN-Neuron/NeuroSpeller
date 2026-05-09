import pygame
from experiment.src.config.app_config import WIDTH, HEIGHT, COLOR_WHITE
from experiment.src.ui.stimulus import SSVEPStimulus

def draw_menu(screen, is_connected):
    screen.fill((0, 0, 0)) 
    
    btn_offline = SSVEPStimulus(x=WIDTH//2 - 350, y=HEIGHT//2 - 100, 
                                size=300, freq=0, label="OFFLINE (Calibration)")
    
    btn_online = SSVEPStimulus(x=WIDTH//2 + 50, y=HEIGHT//2 - 100, 
                               size=300, freq=0, label="ONLINE\n(Speller)")
    
    btn_offline.current_color = (0, 130, 0)
    btn_online.current_color = (130, 0, 0)
    
    btn_offline.draw(screen)
    btn_online.draw(screen)
    
    font = pygame.font.SysFont('Arial', 24)
    text = font.render("Press 1 for Offline or 2 for Online", True, COLOR_WHITE)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 + 250))

    status_font = pygame.font.SysFont('Arial', 20, bold=True)
    if is_connected:
        status_text = status_font.render("Status: Połączono", True, COLOR_WHITE)
    else:
        status_text = status_font.render("Status: Nie połączono", True, (255, 0, 0))
    screen.blit(status_text, (20, 20))

    return btn_offline.rect, btn_online.rect