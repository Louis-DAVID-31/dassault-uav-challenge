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
    
    def update(self, lat, lon, alt, roll, pitch, yaw, gimbal_pitch, gimbal_yaw):
        with self.lock:
            self.lat = lat
            self.lon = lon
            self.alt = alt
            self.roll = roll
            self.pitch = pitch
            self.yaw = yaw
            self.gimbal_pitch = gimbal_pitch
            self.gimbal_yaw = gimbal_yaw

    def get_current_state(self):
        with self.lock:
            return self.lat, self.lon, self.alt, self.roll, self.pitch, self.yaw, self.gimbal_pitch, self.gimbal_yaw