import logging
import os
import warnings

def setup_logging(log_path=None):
    """Unified logging configuration across the application."""
    handlers = [logging.StreamHandler()]
    if log_path:
        dir_name = os.path.dirname(log_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        handlers.append(logging.FileHandler(log_path))
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=handlers,
        force=True
    )
