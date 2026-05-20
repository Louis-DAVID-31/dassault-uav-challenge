import math
import time
from pymavlink import mavutil
from reporting import TerminalDisplay
from .uav_state import UAVState


def calculate_distance_meters(lat1, lon1, lat2, lon2):
    radius = 6378137.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)

    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def coordinates_are_usable(lat, long):
    if (lat is None) or (long is None):
        return False

    return not ((lat == 0) and (long == 0))


def set_guided_mode(STATE: UAVState, TERMINAL: TerminalDisplay, timeout=10):
    master = STATE.get_mavlink(timeout=timeout)
    if master is None:
        TERMINAL.error("MAVLINK", "Could not switch to GUIDED: no MAVLink connection")
        return False

    mode_mapping = master.mode_mapping() or {}
    if "GUIDED" not in mode_mapping:
        TERMINAL.error("MAVLINK", "Could not switch to GUIDED: mode unavailable")
        return False

    guided_mode_id = mode_mapping["GUIDED"]

    with STATE.mavlink_lock:
        master.set_mode(guided_mode_id)

        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=1.0)
            if msg:
                current_mode = master.flightmode
                if current_mode == "GUIDED":
                    TERMINAL.success("MAVLINK", "Matek switched to GUIDED")
                    return True

                master.set_mode(guided_mode_id)
                time.sleep(0.5)

    TERMINAL.error("MAVLINK", "GUIDED command sent but mode change was not confirmed")
    return False


def send_dynamic_waypoint(STATE: UAVState,
                          lat: float,
                          long: float,
                          TERMINAL: TerminalDisplay,
                          label="waypoint",
                          altitude_m: float | None = None,
                          timeout=10):
    if not coordinates_are_usable(lat, long):
        TERMINAL.error("MAVLINK", f"Could not send {label}: coordinates are not usable")
        return False

    master = STATE.get_mavlink(timeout=timeout)
    if master is None:
        TERMINAL.error("MAVLINK", f"Could not send {label}: no MAVLink connection")
        return False

    if altitude_m is None:
        _, _, altitude_m, _, _, _, _, _ = STATE.get_state()

    if altitude_m <= 0:
        TERMINAL.error("MAVLINK", "Could not send waypoint: current relative altitude is not usable")
        return False

    with STATE.mavlink_lock:
        master.mav.command_int_send(
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            mavutil.mavlink.MAV_CMD_DO_REPOSITION,
            0,
            0,
            -1,
            0,
            0,
            math.nan,
            int(lat * 1e7),
            int(long * 1e7),
            altitude_m
        )

    TERMINAL.success("MAVLINK", f"Dynamic {label} sent: {lat}, {long}, alt {altitude_m:.1f}m")
    return True


def wait_until_distance(STATE: UAVState,
                        target_lat: float,
                        target_long: float,
                        trigger_distance_m: float,
                        TERMINAL: TerminalDisplay,
                        label="target",
                        timeout_s=120,
                        check_period_s=0.2):
    if not coordinates_are_usable(target_lat, target_long):
        TERMINAL.error("NAV", f"Could not wait for {label}: coordinates are not usable")
        return False

    TERMINAL.info("NAV", f"Waiting for {label} distance <= {trigger_distance_m:.1f}m")

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        current_lat, current_long, _, _, _, _, _, _ = STATE.get_state()

        if coordinates_are_usable(current_lat, current_long):
            distance_m = calculate_distance_meters(current_lat, current_long, target_lat, target_long)
            if distance_m <= trigger_distance_m:
                TERMINAL.success("NAV", f"{label} distance reached: {distance_m:.1f}m")
                return True

        time.sleep(check_period_s)

    TERMINAL.error("NAV", f"Timeout while waiting for {label} distance")
    return False


def calculate_ballistic_release_distance(altitude_m: float,
                                         ground_speed_m_s: float,
                                         gravity_m_s2=9.80665):
    if altitude_m <= 0 or ground_speed_m_s <= 0:
        return None

    fall_time_s = math.sqrt((2 * altitude_m) / gravity_m_s2)
    return ground_speed_m_s * fall_time_s


def wait_until_ballistic_drop_window(STATE: UAVState,
                                     target_lat: float,
                                     target_long: float,
                                     target_radius_m: float,
                                     TERMINAL: TerminalDisplay,
                                     timeout_s=120,
                                     check_period_s=0.2):
    if not coordinates_are_usable(target_lat, target_long):
        TERMINAL.error("NAV", "Could not wait for drop window: target coordinates are not usable")
        return False

    TERMINAL.info("NAV", f"Waiting for ballistic drop window (target radius {target_radius_m:.1f}m)")

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        current_lat, current_long, altitude_m, _, _, _, _, _ = STATE.get_state()
        ground_speed_m_s = STATE.get_ground_speed()

        if coordinates_are_usable(current_lat, current_long):
            release_distance_m = calculate_ballistic_release_distance(altitude_m, ground_speed_m_s)
            if release_distance_m is not None:
                distance_m = calculate_distance_meters(current_lat, current_long, target_lat, target_long)
                min_distance_m = max(0, release_distance_m - target_radius_m)
                max_distance_m = release_distance_m + target_radius_m

                if min_distance_m <= distance_m <= max_distance_m:
                    TERMINAL.success(
                        "NAV",
                        f"Drop window reached: target {distance_m:.1f}m, release {release_distance_m:.1f}m"
                    )
                    return True

                if distance_m < min_distance_m:
                    TERMINAL.error(
                        "NAV",
                        f"Drop window missed: target {distance_m:.1f}m, release {release_distance_m:.1f}m"
                    )
                    return False

        time.sleep(check_period_s)

    TERMINAL.error("NAV", "Timeout while waiting for ballistic drop window")
    return False


def trigger_servo(STATE: UAVState,
                  servo_channel: int,
                  pwm: int,
                  TERMINAL: TerminalDisplay,
                  timeout=10):
    master = STATE.get_mavlink(timeout=timeout)
    if master is None:
        TERMINAL.error("MAVLINK", "Could not trigger servo: no MAVLink connection")
        return False

    with STATE.mavlink_lock:
        master.mav.command_long_send(
            master.target_system,
            master.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_SERVO,
            0,
            servo_channel,
            pwm,
            0,
            0,
            0,
            0,
            0
        )

    TERMINAL.success("MAVLINK", f"Servo {servo_channel} triggered at PWM {pwm}")
    return True
