import cv2
import numpy as np
import os
import time
from datetime import datetime

# ==========================================
# 1. CONFIGURATION (Edit these before flight)
# ==========================================
SAVE_FOLDER = "verified_markers"
LOG_FOLDER = "logs"
TARGET_IDS = {0, 1, 2, 3, 4}  # Whitelist: Only look for these IDs
MIN_DETECTIONS = 4            # Must be seen this many times...
FRAME_WINDOW = 15             # ...within this many consecutive frames

# ==========================================
# 2. SETUP & LOG FILE INITIALIZATION
# ==========================================
os.makedirs(SAVE_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# Generate a unique log filename based on the current date and time
timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = f"{LOG_FOLDER}/flight_log_{timestamp_str}.txt"

def write_log(message):
    """Helper function to append a line to the text file instantly."""
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")

# Write the Mission Header
write_log("========================================")
write_log("UAV VISION MISSION LOG")
write_log(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
write_log("Camera Resolution: 1920x1080 (Requested)")
write_log(f"Target Whitelist: {list(TARGET_IDS)}")
write_log(f"Sliding Window: {MIN_DETECTIONS} detections within {FRAME_WINDOW} frames")
write_log("========================================")
write_log("TIME, FRAME, ID, EVENT, CONFIDENCE, CENTER_XY, CORNERS, LINKED_IMAGE")

# Setup ArUco
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()
parameters.minMarkerPerimeterRate = 0.005
parameters.maxMarkerPerimeterRate = 4.0
parameters.polygonalApproxAccuracyRate = 0.05
detector = cv2.aruco.ArucoDetector(dictionary, parameters)

# Setup Camera & OpenCV
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920) 
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

# State Variables
seen_markers = set()
detection_history = {}  # Format: {marker_id: [frame1, frame2, ...]}
global_frame_count = 0
start_time = time.time()

print(f"Starting UAV Vision System. Logging to '{LOG_FILE}'...")
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
                write_log(f"{current_time}, {global_frame_count}, {m_id}, DROPPED_TIMEOUT, {len(frames)}/{MIN_DETECTIONS}, NA, NA, NONE")
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
                    write_log(f"{current_time}, {global_frame_count}, {marker_id}, REJECTED_NON_WHITELIST, NA, {center_str}, {corners_str}, NONE")
                    continue 
                
                # 2. Have we already saved it? (IGNORED_DUPLICATE)
                if marker_id in seen_markers:
                    write_log(f"{current_time}, {global_frame_count}, {marker_id}, IGNORED_DUPLICATE, NA, {center_str}, {corners_str}, NONE")
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
                    write_log(f"{current_time}, {global_frame_count}, {marker_id}, VERIFIED, {confidence}/{MIN_DETECTIONS}, {center_str}, {corners_str}, {filename}")
                    
                    seen_markers.add(marker_id)
                    del detection_history[marker_id] # Clear it out since it's verified
                
                # If it hasn't hit the threshold yet, just log that we spotted it
                else:
                    write_log(f"{current_time}, {global_frame_count}, {marker_id}, SPOTTED, {confidence}/{MIN_DETECTIONS}, {center_str}, {corners_str}, NONE")

            # Draw over the live feed
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        # Show windows (Comment these out before actual flight!)
        cv2.imshow('Real Camera View', frame)
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

    write_log("========================================")
    write_log("MISSION SUMMARY")
    write_log(f"End Time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    write_log(f"Total Frames: {global_frame_count}")
    write_log(f"Average FPS: {avg_fps:.2f}")
    write_log(f"Successfully Verified Targets: {list(seen_markers)}")
    write_log("========================================")

    cap.release()
    cv2.destroyAllWindows()
    print(f"Mission shutdown complete. Log saved successfully to: {LOG_FILE}")