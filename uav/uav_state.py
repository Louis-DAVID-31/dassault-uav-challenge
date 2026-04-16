import threading

class UAVState :
    def __init__(self):
        self.lock = threading.Lock()
        
        self.lat = 0.0
        self.lon = 0.0
        self.alt = 0.0
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.gimbal_pitch = 0.0
        self.gimbal_yaw = 0.0

    def get_state(self):
        with self.lock:
            return self.lat, self.lon, self.alt, self.roll, self.pitch, self.yaw, self.gimbal_pitch, self.gimbal_yaw