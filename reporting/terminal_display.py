from core.config_manager import ExecutionConfig

class TerminalDisplay :
    
    def __init__(self, EXECUTION_CONFIG: ExecutionConfig):
        self.enabled = EXECUTION_CONFIG.print_terminal_debug
    
    def print(self, msg: str):
        if self.enabled :
            print(msg)