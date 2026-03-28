import cv2
import numpy as np
import os

# 1. SETUP: Folder and Tracking Logic
SAVE_FOLDER = "verified_markers"
os.makedirs(SAVE_FOLDER, exist_ok=True) 

# --- NEW: THE WHITELIST ---
# Put the exact IDs of the markers you printed here. 
# The drone will completely ignore any ID not in this list.
TARGET_IDS = {0, 1, 2, 3, 4} 
# --------------------------

seen_markers = set()         # IDs we have successfully verified
detection_history = {}       # Sliding window history

# Sliding window thresholds
MIN_DETECTIONS = 4      
FRAME_WINDOW = 15       

# 2. SETUP: ArUco Detector
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()

parameters.minMarkerPerimeterRate = 0.005
parameters.maxMarkerPerimeterRate = 4.0
parameters.polygonalApproxAccuracyRate = 0.05 

detector = cv2.aruco.ArucoDetector(dictionary, parameters)

# 3. SETUP: Camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920) 
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

print("Starting UAV Vision System with Whitelist...")
print(f"Looking ONLY for targets: {TARGET_IDS}")

global_frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    global_frame_count += 1

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    enhanced_gray = clahe.apply(gray)

    # 4. DETECT MARKERS 
    corners, ids, rejected = detector.detectMarkers(enhanced_gray)

    if ids is not None:
        flat_ids = ids.flatten()

        for i, marker_id in enumerate(flat_ids):
            
            # --- THE NEW GATEKEEPER ---
            # If the ID is NOT in our whitelist, skip it immediately.
            if marker_id not in TARGET_IDS:
                continue 
            
            # 5. SLIDING WINDOW LOGIC (Only runs for whitelisted IDs)
            if marker_id not in seen_markers:
                
                if marker_id not in detection_history:
                    detection_history[marker_id] = []
                
                detection_history[marker_id].append(global_frame_count)
                
                # PURGE OLD FRAMES
                detection_history[marker_id] = [
                    f for f in detection_history[marker_id] 
                    if (global_frame_count - f) < FRAME_WINDOW
                ]
                
                # CHECK CONFIDENCE
                if len(detection_history[marker_id]) >= MIN_DETECTIONS:
                    print(f"*** VERIFIED TARGET FOUND! ID: {marker_id} ***")
                    
                    save_frame = frame.copy()
                    cv2.aruco.drawDetectedMarkers(save_frame, [corners[i]], np.array([[marker_id]]))
                    
                    filename = os.path.join(SAVE_FOLDER, f"target_{marker_id}.jpg")
                    cv2.imwrite(filename, save_frame)
                    print(f"Target Screenshot saved to: {filename}")
                    
                    seen_markers.add(marker_id)
                    del detection_history[marker_id]

        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

    # 6. DISPLAY BOTH WINDOWS
    cv2.imshow('Real Camera View', frame)
    cv2.imshow('What OpenCV Processes (CLAHE)', enhanced_gray)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()