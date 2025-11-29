"""Newline IWB Converter - A utility for converting Newline IWB files."""

import importlib.metadata
import logging
import sys

try:
    __version__ = importlib.metadata.version("newline-iwb-converter")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.1.0"


# ANSI color codes
class _ColorFormatter(logging.Formatter):
    """Formatter that adds color to log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        reset = self.RESET
        
        # Format: [LEVEL] message
        record.levelname = f"{level_color}[{record.levelname}]{reset}"
        record.msg = str(record.msg)
        
        return super().format(record)


def configure_logging(level=logging.INFO):
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (default: logging.INFO)
    """
    logger = logging.getLogger("newline_iwb_converter")
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter with just level and message
    formatter = _ColorFormatter("%(levelname)s %(message)s")
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# Configure logging by default at INFO level
logger = configure_logging()
