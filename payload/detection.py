import cv2
import numpy as np
import time
import math
from picamera2 import Picamera2   # type: ignore
from core import ExecutionConfig, Camera, Detection, OutputConfig
from reporting import Log, Detection_Event, TerminalDisplay
from datetime import datetime
from .gps_interpolation import interpolate_gps_location, calculate_distance_meters
from uav import UAVState

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
        self.lat_list = []
        self.long_list = []

    def is_correct_id(self, marker: Marker):
        return self.id == marker.id
    
    def add_coordinates(self, lat, long):
        self.lat_list.append(lat)
        self.long_list.append(long)
    
    def get_final_coordinates(self):
        if not self.long_list :
            return None, None
        return np.mean(self.lat_list), np.mean(self.long_list)

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
              OUTPUT_CONFIG: OutputConfig,
              LOG: Log,
              TERMINAL: TerminalDisplay,
              UAV_STATE: UAVState | None = None):
    
    # ==========================================
    # 1. Setup
    # ==========================================

    start_time = time.time()
    start_datetime = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    # Log Initialisation
    LOG.detection_header(start_datetime, DETECTION, CAMERA)

    # ArUco Setup
    try :
        dict = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, DETECTION.aruco_dict))
        
        param = cv2.aruco.DetectorParameters()
        param.minMarkerPerimeterRate = DETECTION.aruco_param_min_marker_perimeter_rate
        param.maxMarkerPerimeterRate = DETECTION.aruco_param_max_marker_perimeter_rate
        param.polygonalApproxAccuracyRate = DETECTION.aruco_param_polygonal_approx_accuracy_rate
        
        detector = cv2.aruco.ArucoDetector(dict, param)

        clahe = cv2.createCLAHE(clipLimit=DETECTION.clahe_clip_limit, tileGridSize=(8,8))

    except Exception :
        TERMINAL.error("VISION", "Could not setup detector => SHUTTING DOWN")
        return None, None

    # State & Program Variables
    global_frame_count = 0
    
    verified_marker = None
    detection_history = {}

    other_target_history = []

    # Camera Initialisation
    try :
        picam = Picamera2()
        picam_config = picam.create_video_configuration(main={"size": (CAMERA.res_width, CAMERA.res_height)})
        picam.configure(picam_config)
        picam.start()
    except Exception :
        TERMINAL.error("VISION", "Could not start picam => SHUTTING DOWN")
        return None, None
    
    TERMINAL.start_vision()

    # ==========================================
    # 2. MAIN VISION LOOP
    # ==========================================

    try : 
        while True :
            
            # Variables update
            global_frame_count += 1
            frame_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Initialisation
            try:
                frame = picam.capture_array()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                # Image processing
                processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
                if DETECTION.use_clahe :
                    processed_frame = clahe.apply(processed_frame)
                
                # Image analyse
                corners, ids, rejected = detector.detectMarkers(processed_frame)

            except Exception :
                TERMINAL.warning("VISION", "Could not process frame")
                continue


            # Marker result analysis
            if ids is not None:
                flat_ids = ids.flatten()

                # Processing of each marker
                for i, marker_id in enumerate(flat_ids):
                    marker = Marker(marker_id, corners[i][0], DETECTION)

                    # Case : Not a valid marker
                    if not marker.is_valid :
                        LOG.detection_new_marker(Detection_Event.REJECTED_NON_WHITELIST, frame_time, global_frame_count, marker.id, center_str=marker.center_str(), corners_str=marker.corners_str())
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
                            if UAV_STATE is not None:
                                lat, long = interpolate_gps_location(marker.center_x, marker.center_y, CAMERA, UAV_STATE)
                                if (lat is not None) and (long is not None):
                                    verified_marker.add_coordinates(lat, long)
                            LOG.detection_new_marker(Detection_Event.VERIFIED, frame_time, global_frame_count, marker.id, confidence=confidence, center_str=marker.center_str(), corners_str=marker.corners_str(), filename="NONE")
                            TERMINAL.target_found(verified_marker.id)
                        # MARKER SPOTTED
                        else :
                            LOG.detection_new_marker(Detection_Event.SPOTTED, frame_time, global_frame_count, marker.id, confidence=confidence, center_str=marker.center_str(), corners_str=marker.corners_str(), filename="NONE")

                    # Case we track the target 
                    elif verified_marker.is_correct_id(marker) :
                        if calculate_distance_pixels(marker, verified_marker.last_marker)< DETECTION.track_max_dist_pix :
                            if UAV_STATE is None:
                                verified_marker.see_marker(global_frame_count, marker)
                                LOG.detection_new_marker(Detection_Event.TRACKED, frame_time, global_frame_count, marker.id, center_str=marker.center_str(), corners_str=marker.corners_str(), filename="NONE")
                            else:
                                lat, long = interpolate_gps_location(marker.center_x, marker.center_y, CAMERA, UAV_STATE)

                                if (lat is not None) and (long is not None):
                                    if (not verified_marker.long_list) or calculate_distance_meters(verified_marker.lat_list[-1], verified_marker.long_list[-1], lat, long)< DETECTION.track_max_dist_m:
                                        verified_marker.add_coordinates(lat, long)
                                        verified_marker.see_marker(global_frame_count, marker)
                                        LOG.detection_new_marker(Detection_Event.TRACKED, frame_time, global_frame_count, marker.id, center_str=marker.center_str(), corners_str=marker.corners_str(), filename="NONE")
                    
                    # Case another target (we skip it)
                    else :
                        LOG.detection_new_marker(Detection_Event.IGNORED, frame_time, global_frame_count, marker.id, center_str=marker.center_str(), corners_str=marker.corners_str(), filename="NONE")
                        if not (marker.id in other_target_history) :
                            TERMINAL.info("VISION", f"Other target found (id:{marker.id}): IGNORED")
                            other_target_history.append(marker.id)
                        continue

            # Case we lost the target
            if verified_marker is not None :
                if verified_marker.stop_program(global_frame_count,DETECTION) :
                    break

            # Show windows 
            try :
                if EXECUTION_CONFIG.show_real_live_video:
                    cv2.imshow('Real Camera Live Feed', frame)
                if EXECUTION_CONFIG.show_processed_live_video:
                    cv2.imshow('Processed Live Feed', processed_frame)
            except Exception :
                TERMINAL.warning("VISION", "Could not show requested live video feed")

            # Keyboard Loop interruption 
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception:
        TERMINAL.error("VISION", "Could not analyse live feed => SHUTTING DOWN")
        return None, None
    
    # ==========================================
    # 3. SHUTDOWN & SEND RESULTS
    # ==========================================

    finally:
        picam.stop()
        cv2.destroyAllWindows()

        end_time = time.time()
        end_datetime = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        avg_fps = global_frame_count/(end_time-start_time) if (end_time-start_time)>0 else 0

        if verified_marker is not None:
            lat, long = verified_marker.get_final_coordinates()
            id_target_found = verified_marker.id
        else:
            lat, long = None, None
            id_target_found = "NONE"
        
        nb_frames_with_target = (DETECTION.verif_min_detection-1+len(verified_marker.long_list)) if (verified_marker is not None) else 0

        LOG.detection_footer(end_datetime, global_frame_count, avg_fps, id_target_found, nb_frames_with_target, lat, long)
        LOG.clean_detection()

        TERMINAL.end_detection(lat, long)

        # Return the coordinates
        return lat, long
