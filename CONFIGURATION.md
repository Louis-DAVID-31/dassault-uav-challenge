# CONFIGURATION : Parameter Guide

This file defines every configurable parameter for the UAV Vision Payload and GPS interpolation.
No not alter the JSON keys. Only modify the values based on your flight requirements and hardware calibration.

---

* **`mission_control.run_mode`**: String. Defines the execution state. Set to `"flight"` for actual operations (disables hazardous pop-ups), `"ground_test"` for bench testing, or `"simulation"` to mock telemetry data.
* **`mission_control.show_real_live_video`**: Boolean (`true`/`false`). If `true`, opens an OpenCV window displaying the camera feed. **Must be `false` during flight** to prevent the Raspberry Pi from crashing when no monitor is attached.
* **`mission_control.show_processed_live_video`**: Boolean (`true`/`false`). If `true`, opens an OpenCV window displaying the algorithm-processed camera feed. **Must be `false` during flight** to prevent the Raspberry Pi from crashing when no monitor is attached.
* **`mission_control.print_terminal_debug`**: Boolean. If `true`, floods the terminal with every spotted target and logic step. Set to `false` in flight to save CPU cycles.

---

* **`camera_hardware.capture_source`**: Integer or String. Defines the input source for the video feed. `0` usually represents the default camera (e.g., `/dev/video0` on a Raspberry Pi). Can be changed to `1` or `2` for secondary cameras, or set to a string (e.g., `"flight_footage.mp4"`) to test the algorithm on pre-recorded video.
**`camera_hardware.resolution_width`**: Integer. The requested pixel width of the camera feed (e.g., `1920`).
* **`camera_hardware.resolution_height`**: Integer. The requested pixel height of the camera feed (e.g., `1080`).
* **`camera_hardware.camera_matrix`**: 3x3 Array of Floats. The intrinsic lens calibration matrix ($K$). Calculate this using OpenCV's checkerboard calibration. Do not use datasheet estimates.
* **`camera_hardware.distortion_coeffs`**: Array of Floats (5 values). The lens distortion coefficients ($k_1, k_2, p_1, p_2, k_3$) generated alongside the camera matrix.

---

* **`detection_algorithm.target_whitelist`**: Array of Integers. The specific ArUco IDs placed in the field. Any detected ID not in this list is instantly ignored to prevent false positives.
* **`detection_algorithm.aruco_dictionary`**: String. The specific ArUco grid standard used for generation (e.g., `"DICT_4X4_50"`).
* **`detection_algorithm.sliding_window_frames`**: Integer. The time-to-live for a spotted marker. If a marker is lost for this many consecutive frames, its memory is wiped.
* **`detection_algorithm.min_detections_required`**: Integer. How many times a specific marker ID must be seen within the sliding window before it is officially verified and logged.
* **`detection_algorithm.aruco_parameters.min_marker_perimeter_rate`**: Float. The minimum size of a valid marker, expressed as a ratio of the maximum image dimension. `0.005` means the ArUco perimeter must be at least 0.5% of the frame size. Raise this to ignore tiny background noise.
* **`detection_algorithm.aruco_parameters.max_marker_perimeter_rate`**: Float. The maximum size of a valid marker. `4.0` allows the marker to take up massive portions of the screen (useful if flying at very low altitudes or during takeoff/landing).
* **`detection_algorithm.aruco_parameters.polygonal_approx_accuracy_rate`**: Float. Determines how strictly OpenCV requires the detected shape to be a mathematically perfect square. `0.05` allows a 5% margin of error, which is critical for A4 papers that might be slightly bent, taped unevenly, or distorted by the camera lens.
* **`detection_algorithm.image_enhancement.use_clahe`**: Boolean. Toggles the CLAHE (Contrast Limited Adaptive Histogram Equalization) filter. Turn `off` if flying in extremely bright, overexposed sunlight.
* **`detection_algorithm.image_enhancement.clahe_clip_limit`**: Float. The threshold for contrast clipping (default is `2.0`). Higher values create sharper contrast but more digital noise.

---

* **`logging_and_output.log_directory`**: String. The folder path where the `.txt` flight logs are saved (e.g., `"logs/"`).
* **`logging_and_output.image_save_directory`**: String. The folder path where target screenshots are saved (e.g., `"verified_markers/"`).
* **`logging_and_output.save_images_enabled`**: Boolean. If `true`, saves a JPEG every time a target is verified. Set to `false` if SD card I/O speeds are bottlenecking the framerate.
* **`logging_and_output.log_mistakes`**: Boolean. If `true`, records non-whitelisted and dropped targets in the text log for post-flight debugging.