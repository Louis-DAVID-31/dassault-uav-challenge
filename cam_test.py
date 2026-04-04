from picamera2 import Picamera2
import cv2

# Initialisation
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

print("Caméra en direct (Picamera2) ! Appuyez sur 'q' pour quitter.")

try:
    while True:
        # On récupère l'image directement au format OpenCV (tableau NumPy RGB/BGR)
        frame = picam2.capture_array()
        
        cv2.imshow("Flux Picamera2", frame)
        
        if cv2.waitKey(1) == ord('q'):
            break
except Exception as e:
    print(f"Une erreur est survenue : {e}")
finally:
    picam2.stop()
    cv2.destroyAllWindows()