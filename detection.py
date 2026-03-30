import cv2
import numpy as np
import os
import time
from datetime import datetime
import json
from log import Log, Event

# ==========================================
# 1. CONFIGURATION (Edit these before flight)
# ==========================================

print("Loading configuration from config.json...")
try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    print("CRITICAL ERROR: config.json not found! Cannot start vision system.")
    exit(1)

SAVE_FOLDER = config["folders"]["save_folder"]
TARGET_IDS = set(config["algorithm"]["target_ids"])  # Whitelist: Only look for these IDs
MIN_DETECTIONS = config["algorithm"]["min_detections"]           # Must be seen this many times...
FRAME_WINDOW = config["algorithm"]["frame_window"]

# ==========================================
# 2. SETUP & LOG FILE INITIALIZATION
# ==========================================
log = Log(config["folders"]["log_folder"])

os.makedirs(SAVE_FOLDER, exist_ok=True)

log.mission_header(TARGET_IDS, MIN_DETECTIONS, FRAME_WINDOW)

# Setup ArUco
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()
parameters.minMarkerPerimeterRate = config["aruco_parameters"]["minMarkerPerimeterRate"]
parameters.maxMarkerPerimeterRate = config["aruco_parameters"]["maxMarkerPerimeterRate"]
parameters.polygonalApproxAccuracyRate = config["aruco_parameters"]["polygonalApproxAccuracyRate"]
detector = cv2.aruco.ArucoDetector(dictionary, parameters)

# Setup Camera & OpenCV
cap = cv2.VideoCapture(config["camera"]["capture_source"])
cap.set(cv2.CAP_PROP_FRAME_WIDTH, config["camera"]["resolution_width"]) 
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config["camera"]["resolution_height"])
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

# State Variables
seen_markers = set()
detection_history = {}  # Format: {marker_id: [frame1, frame2, ...]}
global_frame_count = 0
start_time = time.time()

print(f"Starting UAV Vision System. Logging to '{log.log_file}'...")
print("Press 'q' in any video window to quit, or Ctrl+C in terminal.")

# ==========================================
# 3. MAIN VISION LOOP
# ==========================================
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from camera.")
            break
        
        global_frame_count += 1
        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        enhanced_gray = clahe.apply(gray)

        # --- A. CHECK FOR TIMEOUTS (DROPPED_TIMEOUT) ---
        # Look at our history. If an active marker hasn't been seen recently, log the drop.
        expired_ids = []
        for m_id, frames in detection_history.items():
            if (global_frame_count - frames[-1]) > FRAME_WINDOW:
                log.log_detection(Event.DROPPED_TIMEOUT,current_time, global_frame_count,m_id,f"{len(frames)/MIN_DETECTIONS:.2f}")
                expired_ids.append(m_id)
        
        # Delete expired memory
        for m_id in expired_ids:
            del detection_history[m_id]

        # --- B. DETECT MARKERS ---
        corners, ids, rejected = detector.detectMarkers(enhanced_gray)

        if ids is not None:
            flat_ids = ids.flatten()

            for i, marker_id in enumerate(flat_ids):
                
                # Format math data for the log file
                c = corners[i][0]
                center_x = int(np.mean(c[:, 0]))
                center_y = int(np.mean(c[:, 1]))
                center_str = f"({center_x}, {center_y})"
                corners_str = f"[[{int(c[0][0])},{int(c[0][1])}],[{int(c[1][0])},{int(c[1][1])}],[{int(c[2][0])},{int(c[2][1])}],[{int(c[3][0])},{int(c[3][1])}]]"

                # 1. Is it a False Positive? (REJECTED_NON_WHITELIST)
                if marker_id not in TARGET_IDS:
                    log.log_detection(Event.REJECTED_NON_WHITELIST,current_time, global_frame_count,marker_id,center_str=center_str, corners_str=corners_str)
                    continue 
                
                # 2. Have we already saved it? (IGNORED_DUPLICATE)
                if marker_id in seen_markers:
                    log.log_detection(Event.IGNORED_DUPLICATE,current_time, global_frame_count,marker_id,center_str=center_str, corners_str=corners_str)
                    continue

                # 3. Active Target Processing (SPOTTED)
                if marker_id not in detection_history:
                    detection_history[marker_id] = []
                
                detection_history[marker_id].append(global_frame_count)
                
                # Purge old frames from memory array
                detection_history[marker_id] = [f for f in detection_history[marker_id] if (global_frame_count - f) <= FRAME_WINDOW]
                confidence = len(detection_history[marker_id])

                # 4. Did it hit the threshold? (VERIFIED)
                if confidence >= MIN_DETECTIONS:
                    print(f"*** VERIFIED TARGET FOUND! ID: {marker_id} ***")
                    
                    # Save Screenshot
                    filename = f"target_{marker_id}_frame_{global_frame_count}.jpg"
                    filepath = os.path.join(SAVE_FOLDER, filename)
                    save_frame = frame.copy()
                    cv2.aruco.drawDetectedMarkers(save_frame, [corners[i]], np.array([[marker_id]]))
                    cv2.imwrite(filepath, save_frame)
                    
                    # Log Verification
                    log.log_detection(Event.VERIFIED,current_time, global_frame_count,marker_id,f"{confidence/MIN_DETECTIONS:.2f}",center_str, corners_str, filename)                    
                    seen_markers.add(marker_id)
                    del detection_history[marker_id] # Clear it out since it's verified
                
                # If it hasn't hit the threshold yet, just log that we spotted it
                else:
                    log.log_detection(Event.SPOTTED,current_time, global_frame_count,marker_id,f"{confidence/MIN_DETECTIONS:.2f}",center_str, corners_str)

            # Draw over the live feed
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        # Show windows (Comment these out before actual flight!)
        if config["live_feed"]["show_real_feed"]:
            cv2.imshow('Real Camera View', frame)
        if config["live_feed"]["show_processed_feed"]:
            cv2.imshow('What OpenCV Processes', enhanced_gray)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Quitting sequence initiated...")
            break

except KeyboardInterrupt:
    print("\nForce quit detected.")

# ==========================================
# 4. SHUTDOWN & LOG SUMMARY
# ==========================================
finally:
    end_time = time.time()
    total_time = end_time - start_time
    # Prevent divide by zero error if quit instantly
    avg_fps = global_frame_count / total_time if total_time > 0 else 0 

    log.mission_footer(global_frame_count, avg_fps, seen_markers)

    cap.release()
    cv2.destroyAllWindows()
    print(f"Mission shutdown complete. Log saved successfully to: {log.log_file}")