import cv2

# 1. SETUP: ArUco Detector
# Using the DICT_4X4_50 dictionary (best for long-distance visibility)
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(dictionary, parameters)

# 2. SETUP: Camera
# '0' is usually the default Raspberry Pi camera index. 
# If you have multiple cameras or a USB cam, it might be 1 or 2.
cap = cv2.VideoCapture(0)

print("Starting Camera... Looking for ArUco markers.")
print("Press 'q' in the video window to quit.")

while True:
    # Read a frame from the camera
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame from camera.")
        break

    # Convert the color frame to grayscale (detection works much better in black & white)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 3. DETECT MARKERS
    # This scans the image for anything that looks like our ArUco dictionary
    corners, ids, rejected = detector.detectMarkers(gray)

    # 4. FRAME THE CODE
    # If at least one marker was found (ids is not None)
    if ids is not None:
        # This single built-in OpenCV function does exactly what you asked for:
        # It draws a distinct colored box around the 4 corners of the detected marker
        # and prints the ID number next to it.
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)
        
        # Optional: Print to the terminal so you know it's working without looking at the screen
        print(f"Detected marker ID(s): {ids.flatten()}")

    # 5. DISPLAY THE VIDEO
    # Show the live feed with the drawn frames
    cv2.imshow('UAV Marker Detection Test', frame)

    # Exit the loop if the 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Quitting...")
        break

# Clean up and turn off the camera
cap.release()
cv2.destroyAllWindows()