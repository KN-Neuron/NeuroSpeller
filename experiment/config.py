
# --- Ustawienia ekranu ---
WIDTH, HEIGHT = 1280, 720
REFRESH_RATE = 60  

# --- Parametry SSVEP ---
# 6 częstotliwości
FREQS = [7.5, 8.57, 10.0, 12.0, 15.0, 8.0] 

# --- Struktura Alfabetu (Drzewo) ---

ALPHABET_TREE = {
    "root": [
        "UNDO", 
        "START", 
        "A B C D\nE F G H\nI J K L\nM N O P", 
        "Q R S T\nU V W X\nY Z + -\n* / ( )", 
        "1 2 3 4\n5 6 7 8\n9 0", 
        "$ & @ \"\n. , ? !\n% : ; =\n~ # Del Blank"
    ],
    
    # Poddrzewo Grupy 1 (Litery A-P)
    "A B C D\nE F G H\nI J K L\nM N O P": [
        "BACK", "MAIN", 
        "A B C D", "E F G H", 
        "I J K L", "M N O P"
    ],
    
    # Poddrzewo Grupy 2 (Litery Q-Z i symbole)
    "Q R S T\nU V W X\nY Z + -\n* / ( )": [
        "BACK", "MAIN", 
        "Q R S T", "U V W X", 
        "Y Z + -", "* / ( )"
    ],
    
    # Poddrzewo Grupy 3 (Cyfry)
    "1 2 3 4\n5 6 7 8\n9 0": [
        "BACK", "MAIN", 
        "1 2", "3 4", 
        "5 6", "7 8 9 0"
    ],
    
    # Liście (konkretne litery) - przykład dla pierwszej grupy
    "A B C D": ["BACK", "MAIN", "A", "B", "C", "D"],
    "E F G H": ["BACK", "MAIN", "E", "F", "G", "H"],
    "I J K L": ["BACK", "MAIN", "I", "J", "K", "L"],
    "M N O P": ["BACK", "MAIN", "M", "N", "O", "P"],
    
    # Przykład dla cyfr
    "1 2": ["BACK", "MAIN", "1", "2", "-", "-"],
}

TILE_MARGIN = 40

MENU_OPTIONS = ["1. OFFLINE", "2. ONLINE"]
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (50, 50, 50)