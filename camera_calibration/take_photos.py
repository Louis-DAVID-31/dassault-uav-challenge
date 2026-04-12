from picamera2 import Picamera2
import cv2
import os
from datetime import datetime

# 1. Configuration du dossier de sauvegarde
save_folder = "images"
if not os.path.exists(save_folder):
    os.makedirs(save_folder)

# 2. Initialisation de Picamera2
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

print("--- Commandes ---")
print("Espace : Prendre une photo")
print("q      : Quitter")

try:
    while True:
        # Récupération du flux en temps réel
        frame = picam2.capture_array()
        
        # Affichage
        cv2.imshow("Flux Picamera2", frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        # Si on appuie sur 'q', on quitte
        if key == ord('q'):
            break
        
        # Si on appuie sur 'Espace' (code 32)
        elif key == 32:
            # Génération d'un nom basé sur la date et l'heure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(save_folder, f"photo_{timestamp}.jpg")
            
            # Enregistrement de l'image (OpenCV utilise le format BGR par défaut)
            # Note : Picamera2 capture souvent en RGB, cv2.imwrite s'attend à du BGR. 
            # On inverse donc les couleurs pour avoir le bon rendu.
            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(filename, bgr_frame)
            
            print(f"Photo enregistrée : {filename}")

except Exception as e:
    print(f"Une erreur est survenue : {e}")

finally:
    picam2.stop()
    cv2.destroyAllWindows()