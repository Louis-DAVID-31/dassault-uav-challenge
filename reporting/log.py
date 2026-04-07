from datetime import datetime
from enum import Enum, auto
import os
from core.config_manager import OutputConfig, ExecutionConfig

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
    def __init__(self, EXECUTION_CONFIG: ExecutionConfig, OUTPUT_CONFIG: OutputConfig):

        self.creation_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_name = f"{EXECUTION_CONFIG.run_mode}_{self.creation_time}"

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
            self.write(f"Date: {self.creation_time}", FILE)
            self.write_separation(FILE)




    def mission_header(self, target_ids, min_detection, frame_window):
        self.write_log("TIME, FRAME, ID, EVENT, CONFIDENCE, CENTER_XY, CORNERS, LINKED_IMAGE")

    def mission_footer(self, global_frame_count, avg_fps, seen_markers):
        self.write_log("========================================")
        self.write_log("MISSION SUMMARY")
        self.write_log(f"End Time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        self.write_log(f"Total Frames: {global_frame_count}")
        self.write_log(f"Average FPS: {avg_fps:.2f}")
        self.write_log(f"Successfully Verified Targets: {list(seen_markers)}")
        self.write_log("========================================")

    def log_detection(self, type, current_time, global_frame_count, marker_id, confidence = "NA", center_str="NA", corners_str="NA", filename="NONE"):
        self.write_log(f"{current_time}, {global_frame_count}, {marker_id}, {type.name}, {confidence}, {center_str}, {corners_str}, {filename}")
    
    def clean_detection(self):
        # Generate output filename (e.g., flight_log_clean.txt)
        base, ext = os.path.splitext(self.detection_log_file)
        output_file = f"{base}_CLEANED{ext}" 
        # These are the events we want to keep. 
        # We keep SPOTTED and VERIFIED to see the progression of a real hit.
        valid_events = ["SPOTTED", "VERIFIED", "TRACKED"]
        cleaned_lines = []
        print(f"Opening {self.detection_log_file} for cleaning...")
        try:
            with open(self.detection_log_file, 'r') as f:
                for line in f:
                    # 1. Always keep headers, footers, and the CSV column labels
                    if line.startswith("=") or "TIME, FRAME, ID" in line or "Date:" in line or "Camera" in line:
                        cleaned_lines.append(line)
                        continue
                    
                    # 2. Check if the line contains a valid event
                    # We split by comma to check the EVENT column (index 3)
                    parts = line.split(',')
                    if len(parts) > 3:
                        event_type = parts[3].strip()
                        if event_type in valid_events:
                            cleaned_lines.append(line)
                    
                    # 3. Keep summary data at the end
                    if any(x in line for x in ["End Time:", "Total Frames:", "Average FPS:", "Successfully"]):
                        cleaned_lines.append(line)

            # Write the filtered data to the new file
            with open(output_file, 'w') as f:
                f.writelines(cleaned_lines)
                
            print(f"Success! Cleaned log saved to: {output_file}")
            print(f"Original size: {os.path.getsize(self.detection_log_file)} bytes")
            print(f"Cleaned size:  {os.path.getsize(output_file)} bytes")

        except FileNotFoundError:
            print(f"Error: The file '{self.detection_log_file}' was not found.")