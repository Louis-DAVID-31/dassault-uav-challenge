import cv2
import time

# --- 1. CONFIGURATION DE LA CAPTURE ---
# Essayez l'index 0. Si ça bloque toujours, changez pour 2, ou -1.
camera_index = 0 
cap = cv2.VideoCapture(camera_index)

# Optimisation pour Raspberry Pi : forcer une résolution raisonnable
# (Évite de saturer la mémoire du Pi avec des images en 4K)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Vérification de l'ouverture
if not cap.isOpened():
    print(f"Erreur : Impossible d'ouvrir la caméra à l'index {camera_index}.")
    print("Astuce : Lancez le script avec 'libcamerify python3 test_camera.py'")
    exit()

print("Démarrage de la capture... Appuyez sur 'q' dans la fenêtre vidéo pour quitter.")

# Variables pour calculer les FPS (Images par seconde)
prev_time = 0

# --- 2. BOUCLE PRINCIPALE (Frame par frame) ---
while True:
    # A. Acquisition de l'image (Frame)
    ret, frame = cap.read()
    
    if not ret:
        print("Erreur : Impossible de lire l'image. Le flux s'est peut-être interrompu.")
        break

    # B. Traitement frame par frame
    # ---------------------------------------------------------
    # Exemple 1 : Conversion en niveaux de gris
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Exemple 2 : Détection de contours (Filtre de Canny)
    # C'est ici que la "vision par ordinateur" opère
    edges = cv2.Canny(gray_frame, 100, 200)
    
    # Calcul des FPS
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time
    
    # Ajout du texte FPS sur l'image d'origine
    cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    # ---------------------------------------------------------

    # C. Affichage des résultats en temps réel
    # On ouvre deux fenêtres pour comparer : la source et le traitement
    cv2.imshow('1 - Flux Original de la Pi Cam', frame)
    cv2.imshow('2 - Traitement (Filtre de Canny)', edges)

    # D. Condition de sortie
    # On attend 1 ms. Si la touche 'q' est pressée, on casse la boucle
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Fermeture demandée par l'utilisateur.")
        break

# --- 3. NETTOYAGE DES RESSOURCES ---
cap.release()
cv2.destroyAllWindows()
print("Ressources libérées, fin du programme.")