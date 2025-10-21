import logging
import sys

def setup_logging(log_file: str = None):
    """
    Set up logging.
    Log to console and optionally to a file.
    """
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=handlers
    )