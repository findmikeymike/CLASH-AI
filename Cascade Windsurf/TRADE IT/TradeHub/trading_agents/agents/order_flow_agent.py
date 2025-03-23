"""
Order Flow Agent - Analyzes order flow at specific price levels.
This agent examines volume, bid/ask imbalances, and order book data
to determine the strength and direction of order flow at key levels.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from loguru import logger
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentState

class OrderFlowData(BaseModel):
    """Model for order flow analysis data."""
    ticker: str
    timeframe: str
    price_level: float
    direction: int  # 1 for bullish, -1 for bearish, 0 for neutral
    strength: float  # 0.0 to 1.0
    volume_profile: Dict[str, Any] = {}
    bid_ask_imbalance: float = 0.0
    delta: float = 0.0
    analysis: Dict[str, Any] = {}

class OrderFlowAgent(BaseAgent):
    """
    Agent responsible for analyzing order flow at specific price levels.
    This agent examines volume, bid/ask imbalances, and order book data
    to determine the strength and direction of order flow at key levels.
    """
    
    def __init__(self, agent_id: str = "order_flow_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the Order Flow Agent."""
        super().__init__(agent_id, config or {})
        config = config or {}
        self.volume_threshold = config.get("volume_threshold", 1.5)  # Multiple of average volume
        self.imbalance_threshold = config.get("imbalance_threshold", 0.2)  # 20% imbalance
    
    async def validate(self, data: Any) -> bool:
        """Validate input data."""
        if not isinstance(data, dict):
            logger.error("Input data must be a dictionary")
            return False
        
        required_fields = ["ticker", "timeframe", "price_level"]
        if not all(field in data for field in required_fields):
            logger.error(f"Missing required fields: {required_fields}")
            return False
        
        return True
    
    async def process(self, data: Dict[str, Any]) -> OrderFlowData:
        """
        Process order flow data at a specific price level.
        
        This method analyzes volume, bid/ask imbalances, and order book data
        to determine the strength and direction of order flow at the specified price level.
        """
        ticker = data["ticker"]
        timeframe = data["timeframe"]
        price_level = data["price_level"]
        
        logger.info(f"Analyzing order flow for {ticker} at price level {price_level}")
        
        # In a real implementation, this would fetch actual order flow data
        # For this example, we'll simulate order flow analysis
        
        # Simulate volume profile analysis
        volume_profile = self._simulate_volume_profile(ticker, price_level)
        
        # Simulate bid/ask imbalance
        bid_ask_imbalance = self._simulate_bid_ask_imbalance(ticker, price_level)
        
        # Simulate delta (difference between buying and selling volume)
        delta = self._simulate_delta(ticker, price_level)
        
        # Determine direction and strength based on analysis
        direction, strength = self._determine_direction_and_strength(
            volume_profile, bid_ask_imbalance, delta
        )
        
        # Create order flow analysis result
        result = OrderFlowData(
            ticker=ticker,
            timeframe=timeframe,
            price_level=price_level,
            direction=direction,
            strength=strength,
            volume_profile=volume_profile,
            bid_ask_imbalance=bid_ask_imbalance,
            delta=delta,
            analysis={
                "volume_significance": volume_profile["significance"],
                "imbalance_significance": abs(bid_ask_imbalance) > self.imbalance_threshold,
                "delta_significance": abs(delta) > 0.3,
                "notes": self._generate_analysis_notes(volume_profile, bid_ask_imbalance, delta)
            }
        )
        
        logger.info(f"Order flow analysis for {ticker}: direction={direction}, strength={strength:.2f}")
        
        return result
    
    def _simulate_volume_profile(self, ticker: str, price_level: float) -> Dict[str, Any]:
        """
        Simulate volume profile analysis.
        
        In a real implementation, this would analyze actual volume data at different price levels.
        """
        # Generate random volume profile for simulation
        # In a real implementation, this would use actual market data
        
        # Simulate volume relative to average
        relative_volume = np.random.uniform(0.5, 3.0)
        
        # Simulate volume distribution (POC = Point of Control)
        poc_offset = np.random.uniform(-0.02, 0.02)
        poc_price = price_level * (1 + poc_offset)
        
        # Determine if volume is significant
        is_significant = relative_volume > self.volume_threshold
        
        return {
            "relative_volume": relative_volume,
            "poc_price": poc_price,
            "value_area_low": poc_price * 0.995,
            "value_area_high": poc_price * 1.005,
            "significance": is_significant,
            "distribution_shape": np.random.choice(["normal", "bimodal", "skewed_up", "skewed_down"]),
            "notes": f"Volume is {'above' if is_significant else 'below'} threshold at {price_level}"
        }
    
    def _simulate_bid_ask_imbalance(self, ticker: str, price_level: float) -> float:
        """
        Simulate bid/ask imbalance.
        
        In a real implementation, this would analyze actual order book data.
        Returns a value between -1.0 (all asks) and 1.0 (all bids).
        """
        # Generate random imbalance for simulation
        # In a real implementation, this would use actual order book data
        return np.random.uniform(-0.5, 0.5)
    
    def _simulate_delta(self, ticker: str, price_level: float) -> float:
        """
        Simulate delta (difference between buying and selling volume).
        
        In a real implementation, this would analyze actual trade data.
        Returns a value between -1.0 (all selling) and 1.0 (all buying).
        """
        # Generate random delta for simulation
        # In a real implementation, this would use actual trade data
        return np.random.uniform(-0.7, 0.7)
    
    def _determine_direction_and_strength(
        self, volume_profile: Dict[str, Any], bid_ask_imbalance: float, delta: float
    ) -> tuple:
        """
        Determine the direction and strength of order flow based on analysis.
        
        Returns a tuple of (direction, strength) where:
        - direction is 1 for bullish, -1 for bearish, 0 for neutral
        - strength is a value between 0.0 and 1.0
        """
        # Calculate direction score (-1.0 to 1.0)
        direction_score = (
            0.4 * bid_ask_imbalance +  # Weight bid/ask imbalance at 40%
            0.6 * delta               # Weight delta at 60%
        )
        
        # Determine direction
        if direction_score > 0.1:
            direction = 1  # Bullish
        elif direction_score < -0.1:
            direction = -1  # Bearish
        else:
            direction = 0  # Neutral
        
        # Calculate strength (0.0 to 1.0)
        raw_strength = (
            0.5 * abs(direction_score) +                    # Direction score magnitude
            0.3 * min(1.0, volume_profile["relative_volume"] / 2) +  # Volume significance
            0.2 * (1.0 if volume_profile["significance"] else 0.3)   # Volume threshold bonus
        )
        
        # Ensure strength is between 0.0 and 1.0
        strength = min(1.0, max(0.0, raw_strength))
        
        return direction, strength
    
    def _generate_analysis_notes(
        self, volume_profile: Dict[str, Any], bid_ask_imbalance: float, delta: float
    ) -> str:
        """Generate analysis notes based on order flow data."""
        notes = []
        
        # Volume notes
        if volume_profile["significance"]:
            notes.append(f"Significant volume ({volume_profile['relative_volume']:.1f}x average)")
        else:
            notes.append(f"Normal volume ({volume_profile['relative_volume']:.1f}x average)")
        
        # Bid/ask imbalance notes
        if bid_ask_imbalance > self.imbalance_threshold:
            notes.append(f"Strong buying pressure (imbalance: {bid_ask_imbalance:.2f})")
        elif bid_ask_imbalance < -self.imbalance_threshold:
            notes.append(f"Strong selling pressure (imbalance: {bid_ask_imbalance:.2f})")
        else:
            notes.append(f"Balanced order book (imbalance: {bid_ask_imbalance:.2f})")
        
        # Delta notes
        if delta > 0.3:
            notes.append(f"Buyers in control (delta: {delta:.2f})")
        elif delta < -0.3:
            notes.append(f"Sellers in control (delta: {delta:.2f})")
        else:
            notes.append(f"Neutral buying/selling (delta: {delta:.2f})")
        
        return " | ".join(notes) 