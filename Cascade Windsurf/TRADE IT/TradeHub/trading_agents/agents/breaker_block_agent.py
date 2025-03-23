"""
Breaker Block Agent - Scans for breaker block setups and retests.
This agent identifies breaker blocks (former support/resistance areas) and
detects when price returns to test these levels.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentState

class PriceLevel(BaseModel):
    """Model for a significant price level."""
    price: float
    type: str  # "support", "resistance", "breaker"
    strength: float  # 0.0 to 1.0
    timeframe: str
    created_at: datetime
    broken_at: Optional[datetime] = None
    touches: int = 1
    
class BreakerBlock(BaseModel):
    """Model for a breaker block."""
    ticker: str
    timeframe: str
    high: float
    low: float
    direction: str  # "bullish" or "bearish"
    strength: float  # 0.0 to 1.0
    created_at: datetime
    broken_at: Optional[datetime] = None
    retested: bool = False
    retest_time: Optional[datetime] = None
    retest_price: Optional[float] = None
    confluence_count: int = 0
    notes: str = ""

class BreakerBlockScan(BaseModel):
    """Model for breaker block scan results."""
    ticker: str
    timestamp: str
    timeframe: str
    price: float
    breaker_blocks: List[BreakerBlock] = []
    active_retests: List[BreakerBlock] = []
    support_resistance_levels: List[PriceLevel] = []
    analysis: Dict[str, Any] = {}

class BreakerBlockAgent(BaseAgent):
    """
    Agent responsible for scanning for breaker block setups and retests.
    
    This agent identifies breaker blocks (former support/resistance areas) and
    detects when price returns to test these levels.
    """
    
    def __init__(self, agent_id: str = "breaker_block_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the Breaker Block Agent."""
        super().__init__(agent_id, config or {})
        config = config or {}
        self.min_touches = config.get("min_touches", 2)  # Minimum touches to consider a level significant
        self.retest_threshold = config.get("retest_threshold", 0.005)  # 0.5% threshold for retest
        self.breaker_blocks = {}  # Dictionary to store breaker blocks by ticker and timeframe
        self.support_resistance = {}  # Dictionary to store support/resistance levels by ticker and timeframe
    
    async def validate(self, data: Any) -> bool:
        """Validate input data."""
        if not isinstance(data, dict):
            logger.error("Input data must be a dictionary")
            return False
        
        required_fields = ["ticker", "timeframe", "ohlc_data"]
        if not all(field in data for field in required_fields):
            logger.error(f"Missing required fields: {required_fields}")
            return False
        
        # Validate OHLC data
        ohlc_data = data["ohlc_data"]
        if not isinstance(ohlc_data, pd.DataFrame):
            logger.error("OHLC data must be a pandas DataFrame")
            return False
        
        required_columns = ["open", "high", "low", "close", "volume"]
        if not all(col.lower() in ohlc_data.columns for col in required_columns):
            logger.error(f"OHLC data must contain columns: {required_columns}")
            return False
        
        return True
    
    async def process(self, data: Dict[str, Any]) -> BreakerBlockScan:
        """
        Process price data to identify breaker blocks and retests.
        
        This method analyzes price data to identify support/resistance levels,
        detect when these levels are broken (creating breaker blocks),
        and identify when price returns to test these breaker blocks.
        """
        ticker = data["ticker"]
        timeframe = data["timeframe"]
        ohlc_data = data["ohlc_data"]
        
        logger.info(f"Scanning for breaker blocks for {ticker} on {timeframe} timeframe")
        
        # Identify support and resistance levels
        support_resistance = self._identify_support_resistance(ticker, timeframe, ohlc_data)
        
        # Update stored support/resistance levels
        self._update_support_resistance(ticker, timeframe, support_resistance)
        
        # Identify breaker blocks
        new_breaker_blocks = self._identify_breaker_blocks(ticker, timeframe, ohlc_data)
        
        # Update stored breaker blocks
        self._update_breaker_blocks(ticker, timeframe, new_breaker_blocks)
        
        # Identify retests of breaker blocks
        active_retests = self._identify_retests(ticker, timeframe, ohlc_data)
        
        # Get current price
        current_price = ohlc_data["close"].iloc[-1]
        
        # Create scan result
        result = BreakerBlockScan(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            timeframe=timeframe,
            price=current_price,
            breaker_blocks=self._get_breaker_blocks(ticker, timeframe),
            active_retests=active_retests,
            support_resistance_levels=self._get_support_resistance(ticker, timeframe),
            analysis=self._generate_analysis(ticker, timeframe, active_retests)
        )
        
        logger.info(f"Breaker block scan for {ticker} on {timeframe}: found {len(active_retests)} active retests")
        
        return result
    
    def _identify_support_resistance(
        self, ticker: str, timeframe: str, ohlc_data: pd.DataFrame
    ) -> List[PriceLevel]:
        """
        Identify support and resistance levels from price data.
        
        This method uses swing highs and lows to identify potential
        support and resistance levels.
        """
        support_resistance = []
        
        # Get high and low prices
        highs = ohlc_data["high"].values
        lows = ohlc_data["low"].values
        closes = ohlc_data["close"].values
        
        # Window size for detecting swing points
        window = 5
        
        # Detect swing highs (resistance)
        for i in range(window, len(highs) - window):
            # Check if this is a local maximum
            if highs[i] == max(highs[i-window:i+window+1]):
                # Calculate strength based on how much higher it is than surrounding bars
                height_diff = np.mean([highs[i] - highs[i-j] for j in range(1, window+1)] + 
                                     [highs[i] - highs[i+j] for j in range(1, window+1)])
                strength = min(1.0, height_diff / (highs[i] * 0.01))  # Normalize to 0-1
                
                # Create resistance level
                level = PriceLevel(
                    price=highs[i],
                    type="resistance",
                    strength=strength,
                    timeframe=timeframe,
                    created_at=ohlc_data.index[i].to_pydatetime(),
                    touches=1
                )
                
                # Check for similar levels and merge if found
                merged = False
                for j, existing_level in enumerate(support_resistance):
                    if (existing_level.type == "resistance" and 
                        abs(existing_level.price - level.price) / level.price < 0.005):
                        # Merge levels
                        support_resistance[j].touches += 1
                        support_resistance[j].strength = max(existing_level.strength, strength)
                        merged = True
                        break
                
                if not merged:
                    support_resistance.append(level)
        
        # Detect swing lows (support)
        for i in range(window, len(lows) - window):
            # Check if this is a local minimum
            if lows[i] == min(lows[i-window:i+window+1]):
                # Calculate strength based on how much lower it is than surrounding bars
                depth_diff = np.mean([lows[i-j] - lows[i] for j in range(1, window+1)] + 
                                    [lows[i+j] - lows[i] for j in range(1, window+1)])
                strength = min(1.0, depth_diff / (lows[i] * 0.01))  # Normalize to 0-1
                
                # Create support level
                level = PriceLevel(
                    price=lows[i],
                    type="support",
                    strength=strength,
                    timeframe=timeframe,
                    created_at=ohlc_data.index[i].to_pydatetime(),
                    touches=1
                )
                
                # Check for similar levels and merge if found
                merged = False
                for j, existing_level in enumerate(support_resistance):
                    if (existing_level.type == "support" and 
                        abs(existing_level.price - level.price) / level.price < 0.005):
                        # Merge levels
                        support_resistance[j].touches += 1
                        support_resistance[j].strength = max(existing_level.strength, strength)
                        merged = True
                        break
                
                if not merged:
                    support_resistance.append(level)
        
        # Filter out weak levels
        support_resistance = [level for level in support_resistance if level.touches >= self.min_touches]
        
        return support_resistance
    
    def _update_support_resistance(
        self, ticker: str, timeframe: str, new_levels: List[PriceLevel]
    ) -> None:
        """Update stored support/resistance levels with new levels."""
        key = f"{ticker}_{timeframe}"
        
        if key not in self.support_resistance:
            self.support_resistance[key] = []
        
        # Merge new levels with existing levels
        for new_level in new_levels:
            merged = False
            for i, existing_level in enumerate(self.support_resistance[key]):
                if (existing_level.type == new_level.type and 
                    abs(existing_level.price - new_level.price) / new_level.price < 0.005):
                    # Merge levels
                    self.support_resistance[key][i].touches = max(existing_level.touches, new_level.touches)
                    self.support_resistance[key][i].strength = max(existing_level.strength, new_level.strength)
                    merged = True
                    break
            
            if not merged:
                self.support_resistance[key].append(new_level)
    
    def _identify_breaker_blocks(
        self, ticker: str, timeframe: str, ohlc_data: pd.DataFrame
    ) -> List[BreakerBlock]:
        """
        Identify breaker blocks from price data.
        
        This method detects when support/resistance levels are broken,
        creating potential breaker blocks.
        """
        breaker_blocks = []
        key = f"{ticker}_{timeframe}"
        
        if key not in self.support_resistance:
            return breaker_blocks
        
        # Get current price data
        current_price = ohlc_data["close"].iloc[-1]
        current_time = ohlc_data.index[-1].to_pydatetime()
        
        # Check for broken support/resistance levels
        for level in self.support_resistance[key]:
            if level.broken_at is None:
                if level.type == "support" and current_price < level.price * 0.99:
                    # Support broken, create bearish breaker block
                    level.broken_at = current_time
                    
                    # Calculate breaker block boundaries
                    # For a broken support, the breaker block is from the support level to a bit above it
                    high = level.price * 1.005
                    low = level.price * 0.995
                    
                    breaker_block = BreakerBlock(
                        ticker=ticker,
                        timeframe=timeframe,
                        high=high,
                        low=low,
                        direction="bearish",
                        strength=level.strength * (level.touches / self.min_touches),
                        created_at=current_time,
                        notes=f"Broken support at {level.price:.2f}"
                    )
                    
                    breaker_blocks.append(breaker_block)
                
                elif level.type == "resistance" and current_price > level.price * 1.01:
                    # Resistance broken, create bullish breaker block
                    level.broken_at = current_time
                    
                    # Calculate breaker block boundaries
                    # For a broken resistance, the breaker block is from the resistance level to a bit below it
                    high = level.price * 1.005
                    low = level.price * 0.995
                    
                    breaker_block = BreakerBlock(
                        ticker=ticker,
                        timeframe=timeframe,
                        high=high,
                        low=low,
                        direction="bullish",
                        strength=level.strength * (level.touches / self.min_touches),
                        created_at=current_time,
                        notes=f"Broken resistance at {level.price:.2f}"
                    )
                    
                    breaker_blocks.append(breaker_block)
        
        return breaker_blocks
    
    def _update_breaker_blocks(
        self, ticker: str, timeframe: str, new_blocks: List[BreakerBlock]
    ) -> None:
        """Update stored breaker blocks with new blocks."""
        key = f"{ticker}_{timeframe}"
        
        if key not in self.breaker_blocks:
            self.breaker_blocks[key] = []
        
        # Add new breaker blocks
        self.breaker_blocks[key].extend(new_blocks)
    
    def _identify_retests(
        self, ticker: str, timeframe: str, ohlc_data: pd.DataFrame
    ) -> List[BreakerBlock]:
        """
        Identify retests of breaker blocks.
        
        This method detects when price returns to test a breaker block.
        """
        active_retests = []
        key = f"{ticker}_{timeframe}"
        
        if key not in self.breaker_blocks:
            return active_retests
        
        # Get current price data
        current_price = ohlc_data["close"].iloc[-1]
        current_time = ohlc_data.index[-1].to_pydatetime()
        
        # Check for retests of breaker blocks
        for i, block in enumerate(self.breaker_blocks[key]):
            if not block.retested:
                # Check if price is retesting the breaker block
                if block.low <= current_price <= block.high:
                    # Price is within the breaker block, this is a retest
                    self.breaker_blocks[key][i].retested = True
                    self.breaker_blocks[key][i].retest_time = current_time
                    self.breaker_blocks[key][i].retest_price = current_price
                    
                    active_retests.append(self.breaker_blocks[key][i])
                
                # Check if price is approaching the breaker block
                elif (block.direction == "bullish" and 
                      block.low - current_price < current_price * self.retest_threshold and
                      block.low > current_price):
                    # Price is approaching a bullish breaker block from below
                    active_retests.append(self.breaker_blocks[key][i])
                
                elif (block.direction == "bearish" and 
                      current_price - block.high < current_price * self.retest_threshold and
                      block.high < current_price):
                    # Price is approaching a bearish breaker block from above
                    active_retests.append(self.breaker_blocks[key][i])
        
        return active_retests
    
    def _get_breaker_blocks(self, ticker: str, timeframe: str) -> List[BreakerBlock]:
        """Get stored breaker blocks for a ticker and timeframe."""
        key = f"{ticker}_{timeframe}"
        return self.breaker_blocks.get(key, [])
    
    def _get_support_resistance(self, ticker: str, timeframe: str) -> List[PriceLevel]:
        """Get stored support/resistance levels for a ticker and timeframe."""
        key = f"{ticker}_{timeframe}"
        return self.support_resistance.get(key, [])
    
    def _generate_analysis(
        self, ticker: str, timeframe: str, active_retests: List[BreakerBlock]
    ) -> Dict[str, Any]:
        """Generate analysis based on breaker blocks and retests."""
        analysis = {
            "has_active_retests": len(active_retests) > 0,
            "retest_count": len(active_retests),
            "strongest_retest": None,
            "directional_bias": "neutral",
            "notes": []
        }
        
        if active_retests:
            # Find strongest retest
            strongest_retest = max(active_retests, key=lambda x: x.strength)
            analysis["strongest_retest"] = {
                "direction": strongest_retest.direction,
                "strength": strongest_retest.strength,
                "price_level": (strongest_retest.high + strongest_retest.low) / 2,
                "created_at": strongest_retest.created_at.isoformat(),
                "notes": strongest_retest.notes
            }
            
            # Determine directional bias
            bullish_retests = [r for r in active_retests if r.direction == "bullish"]
            bearish_retests = [r for r in active_retests if r.direction == "bearish"]
            
            if bullish_retests and not bearish_retests:
                analysis["directional_bias"] = "bullish"
                analysis["notes"].append(f"Found {len(bullish_retests)} bullish breaker block retests")
            elif bearish_retests and not bullish_retests:
                analysis["directional_bias"] = "bearish"
                analysis["notes"].append(f"Found {len(bearish_retests)} bearish breaker block retests")
            elif bullish_retests and bearish_retests:
                # Compare strength
                bullish_strength = sum(r.strength for r in bullish_retests)
                bearish_strength = sum(r.strength for r in bearish_retests)
                
                if bullish_strength > bearish_strength * 1.5:
                    analysis["directional_bias"] = "bullish"
                    analysis["notes"].append("Bullish breaker blocks are significantly stronger")
                elif bearish_strength > bullish_strength * 1.5:
                    analysis["directional_bias"] = "bearish"
                    analysis["notes"].append("Bearish breaker blocks are significantly stronger")
                else:
                    analysis["directional_bias"] = "mixed"
                    analysis["notes"].append("Mixed signals from bullish and bearish breaker blocks")
        else:
            analysis["notes"].append("No active breaker block retests found")
        
        return analysis
    
    def add_confluence(self, ticker: str, timeframe: str, price_level: float, direction: str) -> Tuple[bool, str]:
        """
        Add confluence to a breaker block.
        
        This method is called by other agents to add confluence to a breaker block
        when they detect a setup at a similar price level.
        
        Returns:
            Tuple[bool, str]: Success flag and message
        """
        key = f"{ticker}_{timeframe}"
        
        if key not in self.breaker_blocks:
            return False, f"No breaker blocks found for {ticker} on {timeframe} timeframe"
        
        # Find breaker blocks near the price level
        for i, block in enumerate(self.breaker_blocks[key]):
            # Check if price is within or near the breaker block
            if (block.low * 0.99 <= price_level <= block.high * 1.01 and
                block.direction == direction):
                # Add confluence
                self.breaker_blocks[key][i].confluence_count += 1
                return True, f"Added confluence to {direction} breaker block at {price_level:.2f}"
        
        return False, f"No matching {direction} breaker blocks found near {price_level:.2f}" 