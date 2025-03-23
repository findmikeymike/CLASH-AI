"""
Base Agent - Abstract base class for all trading agents.
This module defines the base agent interface that all specialized agents must implement.
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
import asyncio
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

class AgentState(str, Enum):
    """Enum for agent state."""
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    READY = "ready"

class BaseAgent:
    """
    Abstract base class for all trading agents.
    
    This class defines the interface that all specialized agents must implement.
    It provides common functionality for agent identification, configuration,
    state management, and logging.
    """
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for the agent
            config: Configuration parameters for the agent
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.state = AgentState.IDLE
        self.last_processed = None
        self.last_error = None
        self.processing_history = []
        
        # Set up logging
        logger.info(f"Initializing agent: {self.agent_id}")
    
    async def validate(self, data: Any) -> bool:
        """
        Validate input data before processing.
        
        This method should be overridden by subclasses to implement
        specific validation logic for the agent's input data.
        
        Args:
            data: Input data to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate()")
    
    async def process(self, data: Any) -> Any:
        """
        Process input data and return results.
        
        This method should be overridden by subclasses to implement
        the agent's core processing logic.
        
        Args:
            data: Input data to process
            
        Returns:
            Any: Processing results
        """
        raise NotImplementedError("Subclasses must implement process()")
    
    async def run(self, data: Any) -> Dict[str, Any]:
        """
        Run the agent on input data.
        
        This method handles the execution flow, including validation,
        state management, error handling, and logging.
        
        Args:
            data: Input data to process
            
        Returns:
            Dict[str, Any]: Processing results with metadata
        """
        start_time = datetime.now()
        self.state = AgentState.PROCESSING
        
        try:
            # Validate input data
            is_valid = await self.validate(data)
            if not is_valid:
                self.state = AgentState.ERROR
                self.last_error = "Invalid input data"
                logger.error(f"Agent {self.agent_id}: Invalid input data")
                return {
                    "success": False,
                    "agent_id": self.agent_id,
                    "error": self.last_error,
                    "timestamp": datetime.now().isoformat(),
                    "execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000
                }
            
            # Process data
            result = await self.process(data)
            
            # Update state
            self.state = AgentState.READY
            self.last_processed = datetime.now()
            
            # Record processing history
            self.processing_history.append({
                "timestamp": self.last_processed.isoformat(),
                "data_type": type(data).__name__,
                "result_type": type(result).__name__
            })
            
            # Limit history size
            if len(self.processing_history) > 100:
                self.processing_history = self.processing_history[-100:]
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.info(f"Agent {self.agent_id}: Processing completed in {execution_time:.2f}ms")
            
            # Return results with metadata
            return {
                "success": True,
                "agent_id": self.agent_id,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            # Handle errors
            self.state = AgentState.ERROR
            self.last_error = str(e)
            
            logger.exception(f"Agent {self.agent_id}: Error during processing: {str(e)}")
            
            # Return error information
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": self.last_error,
                "timestamp": datetime.now().isoformat(),
                "execution_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            Dict[str, Any]: Agent status information
        """
        return {
            "agent_id": self.agent_id,
            "state": self.state,
            "last_processed": self.last_processed.isoformat() if self.last_processed else None,
            "last_error": self.last_error,
            "config": self.config,
            "processing_count": len(self.processing_history)
        }
    
    def update_config(self, config_updates: Dict[str, Any]) -> None:
        """
        Update the agent's configuration.
        
        Args:
            config_updates: Dictionary of configuration updates
        """
        self.config.update(config_updates)
        logger.info(f"Agent {self.agent_id}: Configuration updated")
    
    def reset(self) -> None:
        """Reset the agent's state."""
        self.state = AgentState.IDLE
        self.last_error = None
        logger.info(f"Agent {self.agent_id}: State reset to IDLE")
    
    async def shutdown(self) -> None:
        """
        Perform cleanup operations before shutdown.
        
        This method can be overridden by subclasses to implement
        specific cleanup logic.
        """
        logger.info(f"Agent {self.agent_id}: Shutting down")
        # Default implementation does nothing
        pass 