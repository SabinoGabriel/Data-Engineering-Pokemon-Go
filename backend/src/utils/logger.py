"""
Logging utility module for Pokemon GO List Generator.

This module provides a centralized logging configuration with support for:
- Console and file output
- Color-coded log levels
- Configurable log levels and formats
- Automatic log directory creation
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import colorlog
import yaml


class LoggerConfig:
    """Configuration manager for the logging system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize logger configuration.
        
        Args:
            config_path: Path to settings.yaml file. If None, uses default settings.
        """
        self.config = self._load_config(config_path)
    
    def _load_config(self, config_path: Optional[str]) -> dict:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file.
            
        Returns:
            Configuration dictionary.
        """
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
                return full_config.get('logging', {})
        
        # Default configuration
        return {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file_path': 'logs/app.log',
            'console_enabled': True,
            'file_enabled': True
        }


def setup_logger(
    name: str,
    config_path: Optional[str] = None,
    level: Optional[str] = None
) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name: Name of the logger (typically __name__ from calling module).
        config_path: Path to settings.yaml file.
        level: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        
    Returns:
        Configured logger instance.
        
    Example:
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application started")
        >>> logger.error("An error occurred", exc_info=True)
    """
    # Load configuration
    config = LoggerConfig(config_path).config
    
    # Determine log level
    log_level = level or config.get('level', 'INFO')
    log_level = getattr(logging, log_level.upper())
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
    if config.get('console_enabled', True):
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if config.get('file_enabled', True):
        file_path = Path(config.get('file_path', 'logs/app.log'))
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(log_level)
        
        file_formatter = logging.Formatter(
            config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default configuration.
    
    Args:
        name: Name of the logger.
        
    Returns:
        Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


# Example usage and testing
if __name__ == "__main__":
    # Test logger with different levels
    logger = setup_logger(__name__, level="DEBUG")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test with exception
    try:
        1 / 0
    except ZeroDivisionError:
        logger.error("Division by zero occurred", exc_info=True)
