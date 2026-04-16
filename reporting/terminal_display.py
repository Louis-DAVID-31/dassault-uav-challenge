from core import ExecutionConfig
from datetime import datetime
import os

class Colors:
        INFO = '\033[94m'       # Bleu (Informations générales)
        SUCCESS = '\033[92m'    # Vert (Cible validée)
        WARNING = '\033[93m'    # Jaune (Glitch, Perte temporaire)
        ERROR = '\033[91m'      # Rouge (Crash, Perte MAVLink)
        BOLD = '\033[1m'        # Texte en gras
        ENDC = '\033[0m'        # Réinitialisation de la couleur

class TerminalDisplay :
    
    def __init__(self, EXECUTION_CONFIG: ExecutionConfig):
        self.enabled = EXECUTION_CONFIG.print_terminal_debug

    
    def __init__(self, print_enabled: bool):
        self.enabled = print_enabled
    
    def print(self, msg: str):
        if self.enabled :
            print(msg)
    
    def get_time(self):
        return datetime.now().strftime("%H:%M:%S")

    # 1. GENERAL METHODS 

    def info(self, module: str, message: str):
        self.print(f"[{self.get_time()}] {Colors.INFO}[{module}]{Colors.ENDC} {message}")

    def success(self, module: str, message: str):
        self.print(f"[{self.get_time()}] {Colors.SUCCESS}{Colors.BOLD}[{module}] {message}{Colors.ENDC}")

    def warning(self, module: str, message: str):
        self.print(f"[{self.get_time()}] {Colors.WARNING}[{module}] WARNING : {message}{Colors.ENDC}")

    def error(self, module: str, message: str):
        self.print(f"[{self.get_time()}] {Colors.ERROR}{Colors.BOLD}[{module}] ERREUR : {message}{Colors.ENDC}")
    
    def message(self, module: str, message: str):
        self.print(f"[{self.get_time()}] [{module}] {message}")

    def separation(self):
        self.print("========================================")

    # 2. GLOBAL METHODS

    def header(self, mission_start_time, EXECUTION_CONFIG: ExecutionConfig):

        session = f"{EXECUTION_CONFIG.run_mode}_{mission_start_time}"

        os.system('cls' if os.name == 'nt' else 'clear')
        self.separation()
        self.print("UAV MISSION LOG")
        self.print("")
        self.print(f"Session: {session}")
        self.print(f"Date: {mission_start_time}")
        self.separation()

    def footer(self):
        self.separation()
        self.print("SESSION ENDED")
        self.separation()

    # 3. Vision
    def start_vision(self):
        self.info("VISION", "Starting detection system")
    
    def target_found(self, target_id):
        self.success("VISION", f"Target found, id: {target_id}")
        self.info("VISION", f"Starting tracking")
    
    def end_detection(self, lat, long):
        self.info("VISION", f"Target lost")
        self.info("VISION", f"End of detection")
        self.info("VISION", f"Coordinates: {lat}, {long}")
    
    # 4. Mavlink
    def establish_connexion(self):
        self.info("MAVLINK", "Connecting to FC...")
    
    def connexion_established(self):
        self.success("MAVLINK", "Connected to FC")