"""Configuration and environment variable utilities for the hedge fund simulator."""

import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

def load_environment() -> bool:
    """Load environment variables from .env file if it exists.
    
    Returns:
        bool: True if .env file was loaded, False otherwise
    """
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info("Loaded environment variables from .env file")
        return True
    return False

def get_openai_api_key() -> Optional[str]:
    """Get the OpenAI API key from environment variables.
    
    Returns:
        Optional[str]: The API key if found, None otherwise
    """
    return os.getenv('OPENAI_API_KEY')

def is_openai_enabled() -> bool:
    """Check if OpenAI features are enabled.
    
    Returns:
        bool: True if OpenAI features should be enabled
    """
    return os.getenv('USE_OPENAI', 'False').lower() in ('true', '1', 't')

def get_log_level() -> int:
    """Get the logging level from environment variables.
    
    Returns:
        int: The logging level (default: logging.INFO)
    """
    level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    return levels.get(level_str, logging.INFO)

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate the configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    required_sections = [
        'market_data',
        'quant',
        'risk',
        'portfolio',
        'backtest'
    ]
    
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required configuration section: {section}")
            return False
    
    # Add more specific validation as needed
    return True

def setup_logging(log_level: Optional[int] = None) -> None:
    """Set up logging configuration.
    
    Args:
        log_level: Logging level (default: from environment or INFO)
    """
    if log_level is None:
        log_level = get_log_level()
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('hedgefund_simulator.log')
        ]
    )
    
    # Set log level for external libraries
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('yfinance').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger.info("Logging configured")

# Load environment variables when this module is imported
load_environment()
