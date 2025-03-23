"""
Observer that detects confirmed sweep engulfing patterns and stores them in the database.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

logger = logging.getLogger(__name__)

from trading_agents.utils.setup_storage import store_setup
from candle_aggregator import Candle, CandlePatternObserver, PatternType

class SweepEngulfingSetupObserver(CandlePatternObserver):
    """
    Observer that watches for confirmed sweep engulfing patterns and stores them
    in the setup database for display in the dashboard.
    """
    
    def __init__(self):
        """Initialize the observer."""
        super().__init__()
        self.name = "SweepEngulfingSetupObserver"
        logger.info(f"Initialized {self.name}")
    
    def on_pattern_detected(self, pattern_type: PatternType, symbol: str, timeframe: str, 
                           candle: Candle, metadata: Dict[str, Any]) -> None:
        """
        Called when a pattern is detected by the candle aggregator.
        
        Args:
            pattern_type: The type of pattern detected
            symbol: The symbol (ticker) for the pattern
            timeframe: The timeframe of the candle/pattern
            candle: The candle where the pattern was detected
            metadata: Additional information about the pattern
        """
        # We only care about confirmed sweep engulfing patterns
        if pattern_type.name != "SWEEP_ENGULFING_CONFIRMED":
            return
            
        # Extract pattern details from metadata
        direction = metadata.get("direction", "")
        if not direction:
            return
            
        entry_price = metadata.get("entry_price", candle.close)
        stop_loss = metadata.get("stop_loss")
        target = metadata.get("target")
        
        # Calculate risk/reward if possible
        risk_reward = None
        if stop_loss and target and entry_price:
            if direction == "bullish":
                risk = abs(entry_price - stop_loss)
                reward = abs(target - entry_price)
            else:  # bearish
                risk = abs(entry_price - stop_loss)
                reward = abs(entry_price - target)
                
            if risk > 0:
                risk_reward = reward / risk
        
        # Prepare setup data
        setup = {
            "symbol": symbol,
            "setup_type": "sweep_engulfing",
            "direction": direction,
            "timeframe": timeframe,
            "confidence": metadata.get("confidence", 0.7),  # Default confidence
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "target": target,
            "risk_reward": risk_reward,
            "date_identified": datetime.now().isoformat(),
            "status": "active",
            "metadata": {
                "engulf_ratio": metadata.get("engulf_ratio"),
                "sweep_size": metadata.get("sweep_size"),
                "confirmation_type": metadata.get("confirmation_type"),
                "retracement": metadata.get("retracement", False),
                "additional_notes": metadata.get("additional_notes", "")
            }
        }
        
        # Store setup in database
        try:
            setup_id = store_setup(setup)
            logger.info(f"Stored confirmed {direction} sweep engulfing setup (ID: {setup_id}) for {symbol} on {timeframe}")
        except Exception as e:
            logger.error(f"Failed to store sweep engulfing setup: {e}")
