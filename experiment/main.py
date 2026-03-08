import pygame
import sys

pygame.init()

W, H = 800, 500
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("SPELLER")

BLACK = (0, 0, 0)
RED = (200, 30, 30)
GREEN = (50, 180, 50)
WHITE = (255, 255, 255)
DARK_RED = (160, 20, 20)

font_big = pygame.font.SysFont("Arial", 16, bold=True)
font_small = pygame.font.SysFont("Arial", 12)
font_title = pygame.font.SysFont("Arial", 18, bold=True)
font_tile = pygame.font.SysFont("Arial", 20, bold=True)
font_tile_big = pygame.font.SysFont("Arial", 36, bold=True)

# State: which level we're at
# 0 = full keyboard (a)
# 1 = group of 4 letters (b)
# 2 = single letter (c)
state = 0
selected_group = []  # which group was selected in state 0
selected_pair = []   # which pair selected in state 1
typed_word = ""
history = []  # stack for undo: list of (state, selected_group, selected_pair, typed_word)

LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
DIGITS = list("1234567890")
SPECIAL = list("5&@*.,?!%_-=#DelBlank")

def chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]

letter_groups = chunk(LETTERS, 4)  # 7 groups of 4 (last has 2)

def draw_tile(surface, text, x, y, w, h, color, text_color=WHITE, font=None):
    if font is None:
        font = font_big
    pygame.draw.rect(surface, color, (x, y, w, h))
    lines = text.split("\n")
    total_h = len(lines) * (font.get_height() + 2)
    start_y = y + (h - total_h) // 2
    for line in lines:
        surf = font.render(line, True, text_color)
        rect = surf.get_rect(center=(x + w // 2, start_y + font.get_height() // 2))
        surface.blit(surf, rect)
        start_y += font.get_height() + 2

def draw_header(word):
    # Title top right
    t1 = font_title.render("SPELLER", True, WHITE)
    screen.blit(t1, (W - 130, 10))
    t2 = font_title.render(word if word else "SPE", True, RED)
    screen.blit(t2, (W - 130, 32))

def draw_undo_btn():
    draw_tile(screen, "Undo", 20, 20, 90, 50, RED, WHITE, font_big)

def handle_undo():
    global state, selected_group, selected_pair, typed_word
    if history:
        state, selected_group, selected_pair, typed_word = history.pop()

def push_history():
    history.append((state, list(selected_group), list(selected_pair), typed_word))

# ---- DRAW STATE 0: full keyboard ----
def draw_state0():
    screen.fill(BLACK)
    draw_header(typed_word if typed_word else "SPE")
    draw_undo_btn()

    # Letter groups - arranged roughly like image (a)
    # Top area: one group in green (top center)
    positions_letters = [
        (200, 15),   # group 0: ABCD - top center (green)
        (310, 15),   # group 1: EFGH
        (420, 15),   # group 2: IJKL
        (530, 15),   # group 3: MNOP
        (W-130, 60), # group 4: QRST - right side
        (W-130, 120),# group 5: UVWX
        (W-130, 180),# group 6: YZ..
    ]

    for i, grp in enumerate(letter_groups):
        text = " ".join(grp)
        px, py = positions_letters[i]
        color = GREEN if i == 0 else RED
        draw_tile(screen, text, px, py, 100, 45, color, WHITE, font_small)

    # Digits block left side
    digit_text = "1 2 3 4\n5 6 7 8\n9 0"
    draw_tile(screen, digit_text, 20, 120, 110, 70, RED, WHITE, font_small)

    # Special chars block center-bottom
    spec_text = "5 & @ *\n. , ? !\n%  _ - =\n# Del Blank"
    draw_tile(screen, spec_text, 180, 120, 130, 80, RED, WHITE, font_small)

def click_state0(mx, my):
    global state, selected_group
    positions_letters = [
        (200, 15), (310, 15), (420, 15), (530, 15),
        (W-130, 60), (W-130, 120), (W-130, 180),
    ]
    for i, (px, py) in enumerate(positions_letters):
        if px <= mx <= px+100 and py <= my <= py+45:
            push_history()
            selected_group = letter_groups[i]
            state = 1
            return

# ---- DRAW STATE 1: group of 4 split into pairs ----
def draw_state1():
    screen.fill(BLACK)
    grp = selected_group
    draw_header(typed_word if typed_word else "SPE")
    draw_undo_btn()

    # Split into 2 pairs
    pair1 = grp[:2]
    pair2 = grp[2:] if len(grp) > 2 else []

    # 4 large tiles like image (b): top-left, top-right, bottom-left, bottom-right
    pairs_positions = [
        (180, 20, pair1, RED),
        (W-180, 20, pair2, RED) if pair2 else None,
    ]

    # Show all 4 letters as 4 tiles
    tile_w, tile_h = 160, 70
    positions4 = [
        (150, 20),
        (W - 200, 80),
        (30, 220),
        (250, 220),
    ]
    colors4 = [RED, RED, GREEN, RED]

    for i, letter in enumerate(grp):
        if i >= len(positions4):
            break
        px, py = positions4[i]
        # Show pair: two letters per tile
        pass

    # Show as 2-letter pairs
    # pair A B C D => AB | CD
    pairs = [grp[i:i+2] for i in range(0, len(grp), 2)]
    pair_positions = [
        (150, 20, RED),
        (W - 220, 80, RED),
        (30, 220, GREEN),
        (280, 220, RED),
    ]
    for i, pair in enumerate(pairs):
        if i >= len(pair_positions):
            break
        px, py, col = pair_positions[i]
        text = " ".join(pair)
        draw_tile(screen, text, px, py, 160, 65, col, WHITE, font_tile)

def click_state1(mx, my):
    global state, selected_pair
    grp = selected_group
    pairs = [grp[i:i+2] for i in range(0, len(grp), 2)]
    pair_positions = [
        (150, 20), (W - 220, 80), (30, 220), (280, 220),
    ]
    for i, pair in enumerate(pairs):
        if i >= len(pair_positions):
            break
        px, py = pair_positions[i]
        if px <= mx <= px+160 and py <= my <= py+65:
            push_history()
            selected_pair = pair
            state = 2
            return

# ---- DRAW STATE 2: single letters ----
def draw_state2():
    screen.fill(BLACK)
    draw_header(typed_word if typed_word else "SPEL")
    draw_undo_btn()

    pair = selected_pair
    positions = [
        (350, 15, RED),
        (W - 120, 120, RED),
        (30, 300, GREEN),
        (300, 300, RED),
    ]
    for i, letter in enumerate(pair):
        if i >= len(positions):
            break
        px, py, col = positions[i]
        draw_tile(screen, letter, px, py, 130, 100, col, WHITE, font_tile_big)

def click_state2(mx, my):
    global state, typed_word
    pair = selected_pair
    positions = [
        (350, 15), (W - 120, 120), (30, 300), (300, 300),
    ]
    for i, letter in enumerate(pair):
        if i >= len(positions):
            break
        px, py = positions[i]
        if px <= mx <= px+130 and py <= my <= py+100:
            push_history()
            typed_word += letter
            state = 0
            return

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Undo button always available
            if 20 <= mx <= 110 and 20 <= my <= 70:
                handle_undo()
            else:
                if state == 0:
                    click_state0(mx, my)
                elif state == 1:
                    click_state1(mx, my)
                elif state == 2:
                    click_state2(mx, my)

    if state == 0:
        draw_state0()
    elif state == 1:
        draw_state1()
    elif state == 2:
        draw_state2()

    pygame.display.flip()
    clock.tick(60)