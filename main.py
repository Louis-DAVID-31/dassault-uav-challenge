from core import load_config
from reporting import Log, TerminalDisplay
from payload import detection
from uav import UAVState
from uav.telemetry import flight_controller_loop
from datetime import datetime
import threading

# ==========================================
# 1. CONFIGURATION
# ==========================================

START_TIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

EXECUTION_CONFIG, CAMERA, DETECTION, MAVLINK_CONFIG, OUTPUT_CONFIG = load_config("config.json")

LOG = Log(START_TIME, EXECUTION_CONFIG, OUTPUT_CONFIG)
LOG.global_header()

TERMINAL = TerminalDisplay(EXECUTION_CONFIG)
TERMINAL.header(START_TIME, EXECUTION_CONFIG)

TERMINAL.info("SYSTEM", "Config loaded successfully")

UAV_STATE = UAVState()
TELEMETRY_STOP_EVENT = threading.Event()
TELEMETRY_THREAD = threading.Thread(
    target=flight_controller_loop,
    args=(UAV_STATE, LOG, TERMINAL, MAVLINK_CONFIG, OUTPUT_CONFIG, TELEMETRY_STOP_EVENT),
    daemon=True
)
TELEMETRY_THREAD.start()

# ==========================================
# 2. MISSION
# ==========================================

def mission():
    lat, long = detection(EXECUTION_CONFIG, CAMERA, DETECTION, OUTPUT_CONFIG, LOG, TERMINAL, UAV_STATE)

    if (lat is None) or (long is None):
        TERMINAL.error("MISSION", "Coordinates not usable => SHUTTING DOWN")
        return

# ==========================================
# 3. EXECUTION & END OF SESSION
# ==========================================
try :
    mission()

except KeyboardInterrupt:
    TERMINAL.error("SYSTEM", "Mission stopped by operator")

finally :
    TELEMETRY_STOP_EVENT.set()
    TELEMETRY_THREAD.join(timeout=2)

    END_TIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    LOG.global_footer(END_TIME)
    TERMINAL.footer()
