import os
import cv2
import numpy as np

# Prepare your calibration images
chessboard_size = (7, 6)
nb_images = 12 

# Récupère le dossier où se trouve ton script calibration.py
base_path = os.path.dirname(os.path.abspath(__file__))
# Reconstruit le chemin vers tes images
calibration_images = [os.path.join(base_path, "images", f"{i}.jpg") for i in range(nb_images)]

# Arrays to store object points and image points
objpoints = []
imgpoints = []

objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)

# Process each image
for fname in calibration_images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Find the chessboard corners
    ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)
    
    if ret:
        imgpoints.append(corners)
        objpoints.append(objp)

# Calibrate the camera
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

print("Error in projection : \n", ret)
print("\nCamera matrix : \n", mtx)
print("\nDistortion coefficients : \n", dist)
print("\nRotation vector : \n", rvecs)
print("\nTranslation vector : \n", tvecs)