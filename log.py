from datetime import datetime
from enum import Enum, auto
import os

class Event(Enum):
    DROPPED_TIMEOUT = auto()
    REJECTED_NON_WHITELIST = auto()
    IGNORED_DUPLICATE = auto()
    VERIFIED = auto()
    SPOTTED = auto()

class Log:
    def __init__(self, LOG_FOLDER):
        os.makedirs(LOG_FOLDER, exist_ok=True)
        self.log_file = f"{LOG_FOLDER}flight_log_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.txt"

    def write_log(self, message):
        with open(self.log_file, "a") as f:
            f.write(message + "\n")

    def mission_header(self, target_ids, min_detection, frame_window):
        self.write_log("========================================")
        self.write_log("UAV VISION MISSION LOG")
        self.write_log(f"Date: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        self.write_log("Camera Resolution: 1920x1080 (Requested)")
        self.write_log(f"Target Whitelist: {list(target_ids)}")
        self.write_log(f"Sliding Window: {min_detection} detections within {frame_window} frames")
        self.write_log("========================================")
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
    
    def clean_log(self):
        # Generate output filename (e.g., flight_log_clean.txt)
        base, ext = os.path.splitext(self.log_file)
        output_file = f"{base}_CLEANED{ext}" 
        # These are the events we want to keep. 
        # We keep SPOTTED and VERIFIED to see the progression of a real hit.
        valid_events = ["VERIFIED", "SPOTTED"]
        cleaned_lines = []
        print(f"Opening {self.log_file} for cleaning...")
        try:
            with open(self.log_file, 'r') as f:
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
            print(f"Original size: {os.path.getsize(self.log_file)} bytes")
            print(f"Cleaned size:  {os.path.getsize(output_file)} bytes")

        except FileNotFoundError:
            print(f"Error: The file '{self.log_file}' was not found.")
