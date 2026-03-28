import cv2
import numpy as np
import os

# --- CONFIGURATION ---
OUTPUT_FOLDER = "codes"
NUM_MARKERS = 5

# Dimensions A4 à 300 DPI (Standard impression haute qualité)
# Largeur: 210mm -> ~2480 pixels
# Hauteur: 297mm -> ~3508 pixels
A4_WIDTH = 2480
A4_HEIGHT = 3508

# Taille du marker sur la page (en pixels)
# On laisse un peu de marge sur les côtés (2480 - 2000 = 480px de marge totale)
MARKER_SIZE = 2000 

def generate_printable_arucos():
    # 1. Création du dossier
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Dossier '{OUTPUT_FOLDER}' créé.")

    # 2. Chargement du dictionnaire ArUco
    # On utilise DICT_4X4_50
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    print(f"Génération de {NUM_MARKERS} images A4...")

    for marker_id in range(NUM_MARKERS):
        # A. Créer une page blanche (255)
        page = np.full((A4_HEIGHT, A4_WIDTH), 255, dtype=np.uint8)

        # B. Générer le marker brut
        # generateImageMarker renvoie un tableau numpy (noir=0, blanc=255)
        marker_img = cv2.aruco.generateImageMarker(dictionary, marker_id, MARKER_SIZE)

        # C. Calculer la position pour centrer (Offset X et Y)
        x_offset = (A4_WIDTH - MARKER_SIZE) // 2
        y_offset = (A4_HEIGHT - MARKER_SIZE) // 2

        # D. Coller le marker sur la page blanche
        page[y_offset:y_offset+MARKER_SIZE, x_offset:x_offset+MARKER_SIZE] = marker_img

        # E. (Optionnel) Ajouter le texte de l'ID en bas pour l'humain
        text = f"ArUco ID: {marker_id} (DICT_4X4)"
        font_scale = 3
        thickness = 5
        
        # Calcul de la taille du texte pour le centrer
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        text_x = (A4_WIDTH - text_size[0]) // 2
        text_y = y_offset + MARKER_SIZE + 150 # 150px sous le marker

        cv2.putText(page, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 
                    font_scale, (0), thickness, cv2.LINE_AA)

        # F. Sauvegarder
        filename = f"{OUTPUT_FOLDER}/id_{marker_id}.png"
        cv2.imwrite(filename, page)
        
        # Petit log pour suivre l'avancement
        if marker_id % 10 == 0:
            print(f" -> Généré jusqu'à l'ID {marker_id}")

    print("Terminé ! Les images sont dans le dossier 'codes'.")

if __name__ == "__main__":
    generate_printable_arucos()