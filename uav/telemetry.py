import math
import threading
from pymavlink import mavutil
from datetime import datetime
import time
from .uav_state import UAVState
from core import MavlinkConfig, OutputConfig
from reporting import Log, TerminalDisplay

def flight_controller_loop(STATE: UAVState,
                           LOG: Log,
                           TERMINAL: TerminalDisplay,
                           MAVLINK_CONFIG: MavlinkConfig,
                           OUTPUT_CONFIG: OutputConfig,
                           stop_event: threading.Event | None = None):
    TERMINAL.establish_connexion()
    master = None
    state_log_started = False
    
    try:
        master = mavutil.mavlink_connection(MAVLINK_CONFIG.port, baud=MAVLINK_CONFIG.baud)

        while (stop_event is None) or (not stop_event.is_set()):
            if master.wait_heartbeat(timeout=1) is not None:
                break

        if (stop_event is not None) and stop_event.is_set():
            return
        
        STATE.set_mavlink(master)
        TERMINAL.connexion_established()

        with STATE.mavlink_lock:
            master.mav.request_data_stream_send(
                master.target_system, master.target_component,
                mavutil.mavlink.MAV_DATA_STREAM_ALL, MAVLINK_CONFIG.data_freq, 1
            )

        start_datetime = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        LOG.state_header(start_datetime, MAVLINK_CONFIG, OUTPUT_CONFIG)
        state_log_started = True

        last_log_time = time.time()

        while (stop_event is None) or (not stop_event.is_set()):
            with STATE.mavlink_lock:
                msg = master.recv_match(blocking=True, timeout=1)
            if not msg:
                continue

            msg_type = msg.get_type()

            with STATE.lock:
                if msg_type == 'GLOBAL_POSITION_INT':
                    STATE.lat = msg.lat / 1e7
                    STATE.lon = msg.lon / 1e7
                    STATE.alt = msg.relative_alt / 1000.0
                    
                elif msg_type == 'ATTITUDE':
                    STATE.roll = math.degrees(msg.roll)
                    STATE.pitch = math.degrees(msg.pitch)
                    STATE.yaw = math.degrees(msg.yaw)
                    
                elif msg_type == 'MOUNT_STATUS':
                    STATE.gimbal_pitch = msg.pointing_a / 100.0
                    STATE.gimbal_yaw = msg.pointing_c / 100.0
            
            current_time = time.time()
            if (current_time - last_log_time) >= (1.0/OUTPUT_CONFIG.state_log_freq):
                with STATE.lock:
                    frame_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    LOG.state_new_state(frame_time, STATE.lat, STATE.lon, STATE.alt, STATE.roll, STATE.pitch, STATE.yaw, STATE.gimbal_pitch, STATE.gimbal_yaw)
                last_log_time = current_time

    except Exception :
        TERMINAL.error("MAVLINK", "Error in mavlink connexion => SHUTTING DOWN")
        return

    finally:
        if state_log_started:
            end_datetime = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            LOG.state_footer(end_datetime)

        if master is not None:
            STATE.clear_mavlink()
            with STATE.mavlink_lock:
                master.close()
