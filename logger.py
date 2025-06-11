import logging
import sys

def setup_logger(name: str = None):
    logger = logging.getLogger(name)
    if not logger.handlers:  # Prevent duplicate handlers in multi-import scenarios
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)  # Or DEBUG for verbose output
    return logger