import os
import json
import numpy as np
from dataclasses import dataclass

@dataclass
class ExecutionConfig:
    run_mode: str
    show_real_live_video: bool
    show_processed_live_video: bool
    print_terminal_debug: bool

@dataclass
class Camera:
    cap_src: int
    res_width: int
    res_height: int
    matrix: np.ndarray
    dist_coeffs: np.ndarray
    offset_forward: float
    offset_right: float
    offset_down: float

@dataclass
class Detection:
    whitelist: list
    aruco_dict: str

    verif_sliding_window: int 
    verif_min_detection: int
    track_max_dist_pix : float 
    track_max_dist_m : float
    stop_window: int
    
    aruco_param_min_marker_perimeter_rate: float
    aruco_param_max_marker_perimeter_rate: float
    aruco_param_polygonal_approx_accuracy_rate: float 
    use_clahe: bool
    clahe_clip_limit: float

@dataclass
class OutputConfig:
    master_out_dir: str
    log_dir: str
    image_dir: str
    save_images: bool
    log_mistakes: bool

def load_config(path: str):
    # 1. Lecture du fichier JSON
    with open(path, 'r') as config_file:
        config = json.load(config_file)
    
    # 2. Remplissage du bloc Execution
    EXECUTION_CONFIG = ExecutionConfig(
        run_mode = config["mission_control"]["run_mode"],
        show_real_live_video = config["mission_control"]["show_real_live_video"],
        show_processed_live_video = config["mission_control"]["show_processed_live_video"],
        print_terminal_debug = config["mission_control"]["print_terminal_debug"]
    )
    
    # 3. Remplissage du bloc Camera (avec conversion NumPy)
    CAMERA = Camera(
        cap_src = config["camera_hardware"]["capture_source"],
        res_width = config["camera_hardware"]["resolution_width"],
        res_height = config["camera_hardware"]["resolution_height"],
        matrix = np.array(config["camera_hardware"]["camera_matrix"], dtype=np.float64),
        dist_coeffs = np.array(config["camera_hardware"]["distortion_coeffs"], dtype=np.float64),
        offset_forward = config["camera_hardware"]["offset_gps_forward_m"],
        offset_right = config["camera_hardware"]["offset_gps_right_m"],
        offset_down = config["camera_hardware"]["offset_gps_down_m"]
    )

    # 4. Remplissage du bloc Detection
    DETECTION = Detection(
        whitelist = set(config["detection_algorithm"]["target_whitelist"]),
        aruco_dict = config["detection_algorithm"]["aruco_dictionary"],
        verif_sliding_window = config["detection_algorithm"]["verification_sliding_window_frames"],
        verif_min_detection = config["detection_algorithm"]["verification_min_detections_required"],
        stop_window = config["detection_algorithm"]["stopping_window_frames"],
        track_max_dist_pix = config["detection_algorithm"]["tracking_max_distance_pixel"],
        track_max_dist_m = config["detection_algorithm"]["tracking_max_distance_m"],
        aruco_param_min_marker_perimeter_rate = config["detection_algorithm"]["aruco_parameters"]["min_marker_perimeter_rate"],
        aruco_param_max_marker_perimeter_rate = config["detection_algorithm"]["aruco_parameters"]["max_marker_perimeter_rate"],
        aruco_param_polygonal_approx_accuracy_rate = config["detection_algorithm"]["aruco_parameters"]["polygonal_approx_accuracy_rate"],
        use_clahe = config["detection_algorithm"]["image_enhancement"]["use_clahe"],
        clahe_clip_limit = config["detection_algorithm"]["image_enhancement"]["clahe_clip_limit"]
    )

    # 5. Remplissage du bloc Output
    master_dir = config["logging_and_output"]["outputs_directory"]
    
    OUTPUT_CONFIG = OutputConfig(
        master_out_dir = master_dir,
        log_dir = os.path.join(master_dir, config["logging_and_output"]["log_directory"]),
        image_dir = os.path.join(master_dir, config["logging_and_output"]["image_save_directory"]),
        save_images = config["logging_and_output"]["save_images_enabled"],
        log_mistakes = config["logging_and_output"]["log_mistakes"]
    )

    return EXECUTION_CONFIG, CAMERA, DETECTION, OUTPUT_CONFIG