from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd

class BaseAgent(ABC):
    """Base class for all agents in the hedge fund simulator."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the agent with optional configuration.
        
        Args:
            config: Dictionary containing configuration parameters
        """
        self.config = config or {}
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process input data and return the result.
        
        Args:
            data: Input data for processing
            
        Returns:
            Processed output data
        """
        pass
    
    def __call__(self, *args, **kwargs):
        """Make the agent callable."""
        return self.process(*args, **kwargs)
