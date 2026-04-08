from enum import Enum, auto
import os
from core.config_manager import OutputConfig, ExecutionConfig, Detection, Camera

class Detection_Event(Enum):
    REJECTED_NON_WHITELIST = auto()
    SPOTTED = auto()
    VERIFIED = auto()
    TRACKED = auto()

class LogFile(Enum):
    GENERAL = auto()
    STATE = auto()
    DETECTION = auto()

class Log:
    def __init__(self, mission_start_time, EXECUTION_CONFIG: ExecutionConfig, OUTPUT_CONFIG: OutputConfig):

        self.mission_start_time = mission_start_time
        self.log_name = f"{EXECUTION_CONFIG.run_mode}_{self.mission_start_time}"

        self.log_folder = os.path.join(OUTPUT_CONFIG.log_dir,f"{self.log_name}/")
        os.makedirs(self.log_folder, exist_ok=True)
        
        self.general_log_file = os.path.join(self.log_folder, "general_events.txt")
        self.state_log_file = os.path.join(self.log_folder, "uav_state.txt")
        self.detection_log_file = os.path.join(self.log_folder, "detection.txt")

        self.log_mistakes_enabled = OUTPUT_CONFIG.log_mistakes

    def write_general(self, message):
        with open(self.general_log_file, "a") as f:
            f.write(message + "\n")
    
    def write_state(self, message):
         with open(self.state_log_file, "a") as f:
            f.write(message + "\n")

    def write_detection(self, message):
         with open(self.detection_log_file, "a") as f:
            f.write(message + "\n")

    def write(self, msg: str, FILE: LogFile):
        match FILE :
            case LogFile.GENERAL :
                self.write_general(msg)
            case LogFile.STATE :
                self.write_state(msg)
            case LogFile.DETECTION :
                self.write_detection(msg)

    def write_separation(self, FILE: LogFile):
        self.write("========================================", FILE)

    def global_header(self):
        """write a general header in all the files"""
        for FILE in LogFile :
            self.write_separation(FILE)
            self.write("UAV MISSION LOG", FILE)
            self.write("", FILE)
            self.write(f"Session: {self.log_name}", FILE)
            self.write(f"File: {FILE.name}", FILE)
            self.write(f"Date: {self.mission_start_time}", FILE)
            self.write_separation(FILE)

    def detection_header(self, start_time, DETECTION: Detection, CAMERA: Camera):
        self.write_separation(LogFile.DETECTION)
        self.write_detection(f"DETECTION Start Time: {start_time}")
        self.write_detection(f"Camera Resolution: {CAMERA.res_width}x{CAMERA.res_height}")
        self.write_detection(f"Marker Processing Parameters: {DETECTION.verif_sliding_window},{DETECTION.verif_min_detection}, {DETECTION.track_max_dist_pix}, {DETECTION.track_max_dist_m}, {DETECTION.stop_window}")
        self.write_detection(f"Detector Parameters: {DETECTION.aruco_param_min_marker_perimeter_rate}, {DETECTION.aruco_param_max_marker_perimeter_rate}, {DETECTION.aruco_param_polygonal_approx_accuracy_rate}, {DETECTION.use_clahe}, {DETECTION.clahe_clip_limit}")
        self.write_separation(LogFile.DETECTION)
        self.write_detection("TIME, FRAME, ID, EVENT, CONFIDENCE, CENTER_XY, CORNERS, LINKED_IMAGE")

    def detection_new_marker(self, type: Detection_Event, current_time, global_frame_count, marker_id, confidence = "NA", center_str="NA", corners_str="NA", filename="NONE"):
        if (type != Detection_Event.REJECTED_NON_WHITELIST) or (self.log_mistakes_enabled):
            self.write_detection(f"{current_time}, {global_frame_count}, {marker_id}, {type.name}, {confidence}, {center_str}, {corners_str}, {filename}")

    def detection_footer(self, end_time, global_frame_count, avg_fps, id_target_found, nb_frames_with_target, lat_target, long_target):
        self.write_separation(LogFile.DETECTION)
        self.write_detection("DETECTION SUMMARY")
        self.write_detection(f"DETECTION End Time: {end_time}")
        self.write_detection(f"Total Frames: {global_frame_count}")
        self.write_detection(f"Average FPS: {avg_fps:.2f}")
        self.write_detection(f"ID Target Found: {id_target_found}")
        self.write_detection(f"Frames With Target Count: {nb_frames_with_target}")
        self.write_detection(f"Target Coordinates: {lat_target},{long_target}")
        self.write_separation(LogFile.DETECTION)
    
    def clean_detection(self):
        # Generate output filename (e.g., flight_log_clean.txt)
        base, ext = os.path.splitext(self.detection_log_file)
        output_file = f"{base}_CLEANED{ext}" 
        # These are the events we want to keep. 
        # We keep SPOTTED and VERIFIED to see the progression of a real hit.
        valid_events = ["SPOTTED", "VERIFIED", "TRACKED"]
        cleaned_lines = []
        equal_count = 0
        
        with open(self.detection_log_file, 'r') as f:
            for line in f:
                # 1. Always keep headers, footers, and the CSV column labels
                if line.startswith("=") :
                    equal_count += 1

                if equal_count != 3 or line.startswith("=") or "TIME, FRAME, ID":
                    cleaned_lines.append(line)
                    continue
                
                # 2. Check if the line contains a valid event
                # We split by comma to check the EVENT column (index 3)
                parts = line.split(',')
                if len(parts) > 3:
                    event_type = parts[3].strip()
                    if event_type in valid_events:
                        cleaned_lines.append(line)

        # Write the filtered data to the new file
        with open(output_file, 'w') as f:
            f.writelines(cleaned_lines)