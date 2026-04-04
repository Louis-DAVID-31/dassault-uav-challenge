import cv2

# 1. On force le backend V4L2
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

# 2. On force le format d'encodage en MJPEG
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))

# 3. On limite la résolution (très important pour éviter les timeout)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("Erreur d'ouverture")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Échec de la lecture de l'image (timeout ou mauvais format)")
        break
    
    cv2.imshow('Video', frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()