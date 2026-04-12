from core import load_config
from reporting import Log, TerminalDisplay
from payload import detection
from datetime import datetime

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

# ==========================================
# 2. MISSION
# ==========================================

def mission():
    lat, long = detection(EXECUTION_CONFIG, CAMERA, DETECTION, OUTPUT_CONFIG, LOG, TERMINAL)
    
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
    END_TIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    LOG.global_footer(END_TIME)
    TERMINAL.footer()