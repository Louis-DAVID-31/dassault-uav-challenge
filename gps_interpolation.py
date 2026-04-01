import numpy as np
import cv2
import math

def interpolate_gps_location(pixel_x, pixel_y,
                             camera_matrix, dist_coeffs,
                             uav_lat, uav_long, uav_alt,
                             uav_roll, uav_pitch, uav_yaw,
                             gimbal_pitch, gimbal_yaw):
    
    # ---------------------------------------------------------
    # 1. CAMERA FRAME: Convert 2D pixel to 3D Camera Ray
    # ---------------------------------------------------------
    point_2d = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
    undistorted_pt = cv2.undistortPoints(point_2d, camera_matrix, dist_coeffs)[0][0]
    
    # Camera Frame: Z is out the lens, X is image right, Y is image down
    ray_cam = np.array([undistorted_pt[0], undistorted_pt[1], 1.0])
    
    # ---------------------------------------------------------
    # 2. GIMBAL-ZERO FRAME: Align Camera to Plane Belly
    # ---------------------------------------------------------
    # Since Gimbal(0,0) means pointing straight down relative to the plane:
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
    phi = math.radians(uav_roll)
    theta = math.radians(uav_pitch)
    psi = math.radians(uav_yaw)
    
    R_roll = np.array([
        [1, 0, 0],
        [0, math.cos(phi), -math.sin(phi)],
        [0, math.sin(phi), math.cos(phi)]
    ])
    
    R_pitch = np.array([
        [math.cos(theta), 0, math.sin(theta)],
        [0, 1, 0],
        [-math.sin(theta), 0, math.cos(theta)]
    ])
    
    R_yaw = np.array([
        [math.cos(psi), -math.sin(psi), 0],
        [math.sin(psi), math.cos(psi), 0],
        [0, 0, 1]
    ])
    
    # Plane Body to Earth NED rotation
    R_body_to_ned = R_yaw.dot(R_pitch).dot(R_roll)
    ray_ned = R_body_to_ned.dot(ray_body)
    
    # ---------------------------------------------------------
    # 5. SCALE TO GROUND: Intersect ray with flat earth
    # ---------------------------------------------------------
    if ray_ned[2] <= 0:
        # The camera ray is pointing above the horizon. Cannot map to ground.
        return None, None 
        
    scale = uav_alt / ray_ned[2]
    dist_north = ray_ned[0] * scale
    dist_east = ray_ned[1] * scale
    
    # ---------------------------------------------------------
    # 6. CALCULATE FINAL GPS COORDINATES
    # ---------------------------------------------------------
    EARTH_RADIUS = 6378137.0 # WGS84 equatorial radius in meters
    
    lat_offset_rad = dist_north / EARTH_RADIUS
    lon_offset_rad = dist_east / (EARTH_RADIUS * math.cos(math.radians(uav_lat)))
    
    target_lat = uav_lat + math.degrees(lat_offset_rad)
    target_lon = uav_long + math.degrees(lon_offset_rad)
    
    return target_lat, target_lon