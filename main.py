from core.config_manager import load_config, ExecutionConfig, Camera, Detection, OutputConfig
from reporting import Log
from payload import detection
from datetime import datetime

# ==========================================
# 1. CONFIGURATION
# ==========================================

START_TIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

EXECUTION_CONFIG, CAMERA, DETECTION, OUTPUT_CONFIG = load_config("config.json")

LOG = Log(START_TIME, EXECUTION_CONFIG, OUTPUT_CONFIG)
LOG.global_header()

# ==========================================
# 2. DETECTION
# ==========================================

lat, long = detection(EXECUTION_CONFIG, CAMERA, DETECTION, OUTPUT_CONFIG, LOG)
