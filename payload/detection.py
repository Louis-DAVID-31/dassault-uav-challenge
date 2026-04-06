import cv2
import numpy as np
import time
import math
from datetime import datetime
from picamera2 import Picamera2   # type: ignore
from core import ExecutionConfig, Camera, Detection, OutputConfig

class Marker:
    def __init__(self, ID, CORNERS, DETECTION: Detection):
        self.id = ID
        self.corners = CORNERS
        self.center_x = int(np.mean(CORNERS[:, 0]))
        self.center_y = int(np.mean(CORNERS[:, 1]))
        self.is_valid = ID in DETECTION.whitelist
    
    def center_str(self):
        return f"({self.center_x}, {self.center_y})"
    
    def corners_str(self):
        return f"[[{int(self.corners[0][0])},{int(self.corners[0][1])}],[{int(self.corners[1][0])},{int(self.corners[1][1])}],[{int(self.corners[2][0])},{int(self.corners[2][1])}],[{int(self.corners[3][0])},{int(self.corners[3][1])}]]"


class VerifiedMarker:
    def __init__(self, ID, seen_frame, last_marker: Marker):
        self.id = ID
        self.last_seen = seen_frame
        self.last_marker = last_marker
        self.long_list = []
        self.lat_list = []

    def is_correct_id(self, marker: Marker):
        return self.id == marker.id
    
    def add_coordinates(self, long, lat):
        self.long_list.append(long)
        self.lat_list.append(lat)
    
    def get_final_coordinates(self):
        if not self.long_list :
            return None, None
        return np.mean(self.long_list), np.mean(self.lat_list)

    def see_marker(self, frame, marker):
        self.last_seen = frame
        self.last_marker = marker
    
    def stop_program(self, frame, DETECTION : Detection):
        return (frame-self.last_seen)>DETECTION.stop_window


def calculate_distance_pixels(m1: Marker, m2: Marker):
    return math.sqrt((m1.center_x-m2.center_x)**2+(m1.center_y-m2.center_y)**2)


def detection(EXECUTION_CONFIG: ExecutionConfig,
              CAMERA: Camera, 
              DETECTION: Detection, 
              OUTPUT_CONFIG: OutputConfig):
    
    # ==========================================
    # 1. Setup
    # ==========================================

    # ArUco Setup
    dict = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DETECTION.aruco_dict))
    
    param = cv2.aruco.DetectorParameters()
    param.minMarkerPerimeterRate = DETECTION.aruco_param_min_marker_perimeter_rate
    param.maxMarkerPerimeterRate = DETECTION.aruco_param_max_marker_perimeter_rate
    param.polygonalApproxAccuracyRate = DETECTION.aruco_param_polygonal_approx_accuracy_rate
    
    detector = cv2.aruco.ArucoDetector(dict, param)

    clahe = cv2.createCLAHE(clipLimit=DETECTION.clahe_clip_limit, tileGridSize=(8,8))

    # State & Program Variables
    global_frame_count = 0
    rolling_frame_time = time.time()
    
    verified_marker = None
    detection_history = {} 
    
    start_time = time.time()

    # Camera Initialisation
    picam = Picamera2()
    picam_config = picam.create_video_configuration(main={"size": (CAMERA.res_width, CAMERA.res_height)})
    picam.configure(picam_config)
    picam.start()

    # ==========================================
    # 2. MAIN VISION LOOP
    # ==========================================

    try : 
        while True :
            
            # Variables update & FPS
            frame_time = time.time()
            instantaneous_fps = 1.0/max(frame_time-rolling_frame_time, 1e-5)
            rolling_frame_time = frame_time
            global_frame_count += 1

            # Initialisation
            frame = picam.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Image processing
            processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if DETECTION.use_clahe :
                processed_frame = clahe.apply(processed_frame)

            # Image analyse
            corners, ids, rejected = detector.detectMarkers(processed_frame)

            # Marker result analysis
            if ids is not None:
                flat_ids = ids.flatten()

                # Processing of each marker
                for i, marker_id in enumerate(flat_ids):
                    marker = Marker(marker_id, corners[i][0], DETECTION)

                    # Case : Not a valid marker
                    if not marker.is_valid :
                        # REJECTED_NON_WHITELIST
                        continue
                    
                    # We detected a valid marker
                    # Case : No VERIFIED marker yet 
                    if verified_marker is None :
                        if marker_id not in detection_history:
                            detection_history[marker_id] = [] 

                        detection_history[marker.id].append(global_frame_count)
                        
                        # Purge old frames from memory array
                        detection_history[marker.id] = [f for f in detection_history[marker.id] if (global_frame_count - f) <= DETECTION.verif_sliding_window]
                        confidence = len(detection_history[marker.id])
                        
                        # MARKER VERIFIED
                        if confidence >= DETECTION.verif_min_detection:
                            verified_marker =  VerifiedMarker(marker.id, global_frame_count, marker)

                    # Case we track the target 
                    elif verified_marker.is_correct_id(marker) :
                        # New marker in correct target [ADD CONDITION ON METER DISTANCE]
                        if calculate_distance_pixels(marker, verified_marker.last_marker)< DETECTION.track_max_dist_pix :
                            verified_marker.see_marker(global_frame_count, marker)
                    
                    # Case another target (we skip it)
                    else :
                        continue

            # Case we lost the target
            if verified_marker is not None :
                if verified_marker.stop_program(global_frame_count,DETECTION) :
                    break 

            # Show windows 
            if EXECUTION_CONFIG.show_real_live_video:
                cv2.imshow('Real Camera Live Feed', frame)
            if EXECUTION_CONFIG.show_processed_live_video:
                cv2.imshow('Processed Live Feed', processed_frame)
            
            # Loop interruption
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception:
        pass
    
    # ==========================================
    # 3. SHUTDOWN & SEND RESULTS
    # ==========================================

    finally:
        picam.stop()
        cv2.destroyAllWindows()

    # Return the coordinates
    if verified_marker is not None :
        return verified_marker.get_final_coordinates()
    return None, None