import logging
import sys
from pathlib import Path

# The project root is two levels up from lib/
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "data" / "logs"

def setup_app_logger(name, log_file_name):
    """Sets up a logger that writes to a file and the console."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file_path = LOG_DIR / log_file_name

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False # Prevent double logging

    # Clear existing handlers to avoid duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file_path, encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s | %(message)s'))
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(ch)

    return logger

def setup_debug_logger():
    """Sets up a dedicated logger for API debugging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    debug_log_file = LOG_DIR / 'bexio-api-debug.log'
    
    debug_logger = logging.getLogger('bexio_api_debug')
    debug_logger.setLevel(logging.DEBUG)
    debug_logger.propagate = False
    
    fh = logging.FileHandler(debug_log_file, mode='a', encoding='utf-8')
    fh.setFormatter(logging.Formatter('--- %(asctime)s ---\n%(message)s\n\n'))
    
    if debug_logger.hasHandlers():
        debug_logger.handlers.clear()
    
    debug_logger.addHandler(fh)
    return debug_logger
