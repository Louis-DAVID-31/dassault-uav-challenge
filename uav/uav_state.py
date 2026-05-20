import threading

class UAVState :
    def __init__(self):
        self.lock = threading.Lock()
        self.mavlink_lock = threading.Lock()
        self.mavlink_connected = threading.Event()
        self.mavlink = None
        
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

    def set_mavlink(self, mavlink):
        with self.mavlink_lock:
            self.mavlink = mavlink
            self.mavlink_connected.set()

    def clear_mavlink(self):
        with self.mavlink_lock:
            self.mavlink = None
            self.mavlink_connected.clear()

    def get_mavlink(self, timeout=None):
        if not self.mavlink_connected.wait(timeout):
            return None

        with self.mavlink_lock:
            return self.mavlink
