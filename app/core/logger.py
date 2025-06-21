"""
Centralized logging configuration for LifeBuddy.
Provides both console and file logging with proper formatting.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Log format with timestamps and context
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Console format with emojis for better UX
CONSOLE_FORMAT = "%(levelname_emoji)s %(message)s"

class EmojiFormatter(logging.Formatter):
    """Custom formatter that adds emojis to log levels for console output."""
    
    EMOJI_MAP = {
        'DEBUG': '🔍',
        'INFO': '📝',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '💥'
    }
    
    def format(self, record):
        # Add emoji to the record
        record.levelname_emoji = self.EMOJI_MAP.get(record.levelname, '📝')
        return super().format(record)

def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with both console and file handlers.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional specific log file name (defaults to app.log)
        console_output: Whether to output to console
        file_output: Whether to output to file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler with emoji formatting
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Console shows INFO and above
        console_formatter = EmojiFormatter(CONSOLE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with detailed formatting
    if file_output:
        log_file = log_file or "app.log"
        file_path = LOGS_DIR / log_file
        
        # Use rotating file handler to prevent huge log files
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # File logs everything
        file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str, **kwargs) -> logging.Logger:
    """
    Convenience function to get a configured logger.
    
    Args:
        name: Logger name (usually __name__)
        **kwargs: Additional arguments for setup_logger
        
    Returns:
        Configured logger instance
    """
    return setup_logger(name, **kwargs)

# Pre-configured loggers for common components
def get_health_logger() -> logging.Logger:
    """Get logger for health data processing."""
    return setup_logger("lifebuddy.health", log_file="health_processing.log")

def get_api_logger() -> logging.Logger:
    """Get logger for FastAPI backend."""
    return setup_logger("lifebuddy.api", log_file="fastapi.log")

def get_ui_logger() -> logging.Logger:
    """Get logger for Streamlit UI."""
    return setup_logger("lifebuddy.ui", log_file="streamlit.log")

def get_ollama_logger() -> logging.Logger:
    """Get logger for Ollama interactions."""
    return setup_logger("lifebuddy.ollama", log_file="ollama.log")

def get_agent_logger() -> logging.Logger:
    """Get logger for AI agents."""
    return setup_logger("lifebuddy.agents", log_file="agents.log")

# Configure root logger to capture everything
def configure_root_logger(level: str = "INFO"):
    """Configure the root logger for the entire application."""
    root_logger = logging.getLogger()
    
    # Don't configure if already done
    if root_logger.handlers:
        return
        
    root_logger.setLevel(logging.DEBUG)
    
    # Add handlers to capture all logs
    setup_logger("lifebuddy.root", level=level, log_file="app.log")

# Auto-configure when imported
configure_root_logger(level=os.getenv("LOG_LEVEL", "INFO")) 