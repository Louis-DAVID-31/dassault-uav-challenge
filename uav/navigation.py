import math
import time
from pymavlink import mavutil
from reporting import TerminalDisplay
from .uav_state import UAVState


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
                          altitude_m: float | None = None,
                          timeout=10):
    master = STATE.get_mavlink(timeout=timeout)
    if master is None:
        TERMINAL.error("MAVLINK", "Could not send waypoint: no MAVLink connection")
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

    TERMINAL.success("MAVLINK", f"Dynamic waypoint sent: {lat}, {long}, alt {altitude_m:.1f}m")
    return True
