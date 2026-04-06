from core.config_manager import load_config, ExecutionConfig, Camera, Detection, OutputConfig

# ==========================================
# 1. CONFIGURATION
# ==========================================

EXECUTION_CONFIG, CAMERA, DETECTION, OUTPUT_CONFIG = load_config("config.json")

# ==========================================
# 2. DETECTION
# ==========================================