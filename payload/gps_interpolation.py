import numpy as np
import cv2
import math
from uav import UAVState
from core import Camera

def interpolate_gps_location(pixel_x, pixel_y,
                             CAMERA: Camera,
                             UAV_STATE: UAVState):
    
    # Récupération instantanée des données de vol (depuis la mémoire partagée)
    lat, lon, alt, roll, pitch, yaw, gimbal_pitch, gimbal_yaw = UAV_STATE.get_current_state()

    # ---------------------------------------------------------
    # 1. CAMERA FRAME: Convert 2D pixel to 3D Camera Ray
    # ---------------------------------------------------------
    point_2d = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
    undistorted_pt = cv2.undistortPoints(point_2d, CAMERA.matrix, CAMERA.dist_coeffs)[0][0]
    
    # Camera Frame: Z is out the lens, X is image right, Y is image down
    ray_cam = np.array([undistorted_pt[0], undistorted_pt[1], 1.0])
    
    # ---------------------------------------------------------
    # 2. GIMBAL-ZERO FRAME: Align Camera to Plane Belly
    # ---------------------------------------------------------
    # Camera Z (Out) -> Points Body Z (Down)
    # Camera X (Image Right) -> Points Body Y (Right Wing)
    # Camera Y (Image Bottom) -> Points Body -X (Towards Tail)
    R_cam_to_g0 = np.array([
        [ 0, -1,  0],
        [ 1,  0,  0],
        [ 0,  0,  1]
    ])
    ray_g0 = R_cam_to_g0.dot(ray_cam)
    
    # ---------------------------------------------------------
    # 3. PLANE BODY FRAME: Apply Gimbal Angles
    # ---------------------------------------------------------
    gp = math.radians(gimbal_pitch)
    gy = math.radians(gimbal_yaw)
    
    # Gimbal Pitch (Rotation around plane's Y axis / wings)
    R_g_pitch = np.array([
        [math.cos(gp), 0, math.sin(gp)],
        [0, 1, 0],
        [-math.sin(gp), 0, math.cos(gp)]
    ])
    
    # Gimbal Yaw (Rotation around plane's Z axis / belly)
    R_g_yaw = np.array([
        [math.cos(gy), -math.sin(gy), 0],
        [math.sin(gy), math.cos(gy), 0],
        [0, 0, 1]
    ])
    
    # Combine gimbal rotations and apply to our ray
    ray_body = R_g_yaw.dot(R_g_pitch).dot(ray_g0)
    
    # ---------------------------------------------------------
    # 4. EARTH NED FRAME: Apply UAV Attitude (Roll, Pitch, Yaw)
    # ---------------------------------------------------------
    phi = math.radians(roll)
    theta = math.radians(pitch)
    psi = math.radians(yaw)
    
    # Roll (Rotation around X axis)
    R_roll = np.array([
        [1, 0, 0],
        [0, math.cos(phi), -math.sin(phi)],
        [0, math.sin(phi), math.cos(phi)]
    ])
    
    # Pitch (Rotation around Y axis)
    R_pitch = np.array([
        [math.cos(theta), 0, math.sin(theta)],
        [0, 1, 0],
        [-math.sin(theta), 0, math.cos(theta)]
    ])
    
    # Yaw (Rotation around Z axis)
    R_yaw = np.array([
        [math.cos(psi), -math.sin(psi), 0],
        [math.sin(psi), math.cos(psi), 0],
        [0, 0, 1]
    ])
    
    # Plane Body to Earth NED rotation
    R_body_to_ned = R_yaw.dot(R_pitch).dot(R_roll)
    ray_ned = R_body_to_ned.dot(ray_body)
    
    # =========================================================
    # 4.5. THE LEVER ARM: Apply Camera Physical Offset
    # =========================================================
    # Put the physical offset (Forward, Right, Down) into a vector
    camera_offset_body = np.array([CAMERA.offset_forward, CAMERA.offset_right, CAMERA.offset_down])
    
    # Rotate the physical offset into the Earth (NED) frame
    camera_offset_ned = R_body_to_ned.dot(camera_offset_body)
    
    # =========================================================
    # 5. SCALE TO GROUND: Intersect ray with flat earth
    # =========================================================
    if ray_ned[2] <= 0:
        # The camera ray is pointing above the horizon. Cannot map to ground.
        return None, None 
        
    # Calculate the TRUE altitude of the camera lens (GPS altitude minus camera's Z displacement)
    true_alt = alt - camera_offset_ned[2]
    
    if true_alt <= 0:
        return None, None # Safety check (UAV crashed or math error)

    # Scale the ray based on the camera's true altitude
    scale = true_alt / ray_ned[2]
    
    # Add the camera's starting position (offset_ned) to the ray's travel distance
    dist_north = camera_offset_ned[0] + (ray_ned[0] * scale)
    dist_east = camera_offset_ned[1] + (ray_ned[1] * scale)
    
    # ---------------------------------------------------------
    # 6. CALCULATE FINAL GPS COORDINATES
    # ---------------------------------------------------------
    EARTH_RADIUS = 6378137.0 # WGS84 equatorial radius in meters
    
    # Convert meters to radians
    lat_offset_rad = dist_north / EARTH_RADIUS
    lon_offset_rad = dist_east / (EARTH_RADIUS * math.cos(math.radians(lat)))
    
    # Add offsets to original drone GPS position
    target_lat = lat + math.degrees(lat_offset_rad)
    target_lon = lon + math.degrees(lon_offset_rad)
    
    return target_lat, target_lon


def calculate_distance_meters(lat1, lon1, lat2, lon2):
    """Calculates distance between two GPS points in meters using Haversine."""
    R = 6378137.0 # Earth radius in meters
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c