from core import load_config
from reporting import Log, TerminalDisplay
from payload import detection
from uav import UAVState
from uav.navigation import send_dynamic_waypoint, set_guided_mode, trigger_servo, wait_until_ballistic_drop_window, wait_until_distance
from uav.telemetry import flight_controller_loop
from datetime import datetime
import threading

# ==========================================
# 1. CONFIGURATION
# ==========================================

START_TIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

EXECUTION_CONFIG, CAMERA, DETECTION, MAVLINK_CONFIG, DELIVERY_CONFIG, OUTPUT_CONFIG = load_config("config.json")

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

    _, _, mission_altitude_m, _, _, _, _, _ = UAV_STATE.get_state()

    if not set_guided_mode(UAV_STATE, TERMINAL):
        TERMINAL.error("MISSION", "Could not switch Matek to GUIDED => SHUTTING DOWN")
        return

    if not send_dynamic_waypoint(UAV_STATE,
                                 DELIVERY_CONFIG.ground_station_lat,
                                 DELIVERY_CONFIG.ground_station_long,
                                 TERMINAL,
                                 label="base waypoint",
                                 altitude_m=mission_altitude_m):
        TERMINAL.error("MISSION", "Could not send base waypoint => SHUTTING DOWN")
        return

    if not wait_until_distance(UAV_STATE,
                               DELIVERY_CONFIG.ground_station_lat,
                               DELIVERY_CONFIG.ground_station_long,
                               DELIVERY_CONFIG.base_acceptance_radius_m,
                               TERMINAL,
                               label="base",
                               timeout_s=DELIVERY_CONFIG.waypoint_timeout_s,
                               check_period_s=DELIVERY_CONFIG.distance_check_period_s):
        TERMINAL.error("MISSION", "Base waypoint was not reached => SHUTTING DOWN")
        return

    if not send_dynamic_waypoint(UAV_STATE,
                                 lat,
                                 long,
                                 TERMINAL,
                                 label="target waypoint",
                                 altitude_m=mission_altitude_m):
        TERMINAL.error("MISSION", "Could not send target waypoint => SHUTTING DOWN")
        return

    if not wait_until_ballistic_drop_window(UAV_STATE,
                                            lat,
                                            long,
                                            DELIVERY_CONFIG.target_radius_m,
                                            TERMINAL,
                                            timeout_s=DELIVERY_CONFIG.drop_timeout_s,
                                            check_period_s=DELIVERY_CONFIG.distance_check_period_s):
        TERMINAL.error("MISSION", "Drop window was not reached => SHUTTING DOWN")
        return

    if not trigger_servo(UAV_STATE, DELIVERY_CONFIG.drop_servo_channel, DELIVERY_CONFIG.drop_servo_pwm, TERMINAL):
        TERMINAL.error("MISSION", "Could not trigger drop servo => SHUTTING DOWN")
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
