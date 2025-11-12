import os
import logging
from pathlib import Path

def setup_logging(name: str = None) -> logging.Logger:
    """
    Setup logging configuration with environment variable support
    
    Args:
        name: Optional logger name. If None, returns root logger
    
    Returns:
        Configured logger instance
    """
    # Get log path from environment or use default
    log_path = os.getenv("LOG_PATH", "logs/app.log")
    
    # Ensure log directory exists
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(name)s] [%(levelname)s] [%(module)s:%(funcName)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),  # prints to console
        ],
    )
    
    # Get logger
    logger = logging.getLogger(name) if name else logging.getLogger()
    
    # Log startup message
    logger.info(f"Logging initialized. Writing to {log_path}")
    
    return logger