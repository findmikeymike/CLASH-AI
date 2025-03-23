"""
Fair Value Gap Agent - Scans for fair value gaps in price action.
This agent identifies fair value gaps (FVGs) where price moves rapidly,
leaving an imbalance or gap in the market that may be filled later.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentState

class FairValueGap(BaseModel):
    """Model for a fair value gap."""
    ticker: str
    timeframe: str
    high: float
    low: float
    direction: str  # "bullish" or "bearish"
    strength: float  # 0.0 to 1.0
    created_at: datetime
    filled: bool = False
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None
    age_in_bars: int = 0
    confluence_count: int = 0
    notes: str = ""

class FVGScan(BaseModel):
    """Model for fair value gap scan results."""
    ticker: str
    timestamp: str
    timeframe: str
    price: float
    fvgs: List[FairValueGap] = []
    active_fvgs: List[FairValueGap] = []
    analysis: Dict[str, Any] = {}

class FVGAgent(BaseAgent):
    """
    Agent responsible for scanning for fair value gaps.
    
    This agent identifies fair value gaps (FVGs) where price moves rapidly,
    leaving an imbalance or gap in the market that may be filled later.
    """
    
    def __init__(self, agent_id: str = "fvg_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the Fair Value Gap Agent."""
        super().__init__(agent_id, config or {})
        config = config or {}
        self.min_gap_size = config.get("min_gap_size", 0.003)  # Minimum gap size as percentage of price
        self.max_age = config.get("max_age", 100)  # Maximum age in bars to track FVGs
        self.fvgs = {}  # Dictionary to store FVGs by ticker and timeframe
    
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
    
    async def process(self, data: Dict[str, Any]) -> FVGScan:
        """
        Process price data to identify fair value gaps.
        
        This method analyzes price data to identify fair value gaps (FVGs),
        update existing FVGs, and check if any FVGs have been filled.
        """
        ticker = data["ticker"]
        timeframe = data["timeframe"]
        ohlc_data = data["ohlc_data"]
        
        logger.info(f"Scanning for fair value gaps for {ticker} on {timeframe} timeframe")
        
        # Identify new FVGs
        new_fvgs = self._identify_fvgs(ticker, timeframe, ohlc_data)
        
        # Update stored FVGs
        self._update_fvgs(ticker, timeframe, new_fvgs, ohlc_data)
        
        # Check for filled FVGs
        active_fvgs = self._check_filled_fvgs(ticker, timeframe, ohlc_data)
        
        # Get current price
        current_price = ohlc_data["close"].iloc[-1]
        
        # Create scan result
        result = FVGScan(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            timeframe=timeframe,
            price=current_price,
            fvgs=self._get_fvgs(ticker, timeframe),
            active_fvgs=active_fvgs,
            analysis=self._generate_analysis(ticker, timeframe, active_fvgs)
        )
        
        logger.info(f"FVG scan for {ticker} on {timeframe}: found {len(new_fvgs)} new FVGs, {len(active_fvgs)} active FVGs")
        
        return result
    
    def _identify_fvgs(
        self, ticker: str, timeframe: str, ohlc_data: pd.DataFrame
    ) -> List[FairValueGap]:
        """
        Identify fair value gaps from price data.
        
        This method looks for gaps in price action where a candle's low is higher
        than the previous candle's high (bullish FVG) or a candle's high is lower
        than the previous candle's low (bearish FVG).
        """
        fvgs = []
        
        # Need at least 3 candles to identify FVGs
        if len(ohlc_data) < 3:
            return fvgs
        
        # Get price data
        highs = ohlc_data["high"].values
        lows = ohlc_data["low"].values
        closes = ohlc_data["close"].values
        
        # Look for FVGs in the most recent data
        # We look at the last 3 candles (candles at index -3, -2, and -1)
        
        # Check for bullish FVG (low of candle -1 > high of candle -3)
        if lows[-1] > highs[-3]:
            # Calculate gap size as percentage of price
            gap_size = (lows[-1] - highs[-3]) / highs[-3]
            
            # Only consider gaps larger than minimum size
            if gap_size >= self.min_gap_size:
                # Calculate strength based on gap size and volume
                strength = min(1.0, gap_size * 100)  # Normalize to 0-1
                
                # Create bullish FVG
                fvg = FairValueGap(
                    ticker=ticker,
                    timeframe=timeframe,
                    high=lows[-1],
                    low=highs[-3],
                    direction="bullish",
                    strength=strength,
                    created_at=ohlc_data.index[-1].to_pydatetime(),
                    notes=f"Bullish FVG: {gap_size:.2%} gap"
                )
                
                fvgs.append(fvg)
        
        # Check for bearish FVG (high of candle -1 < low of candle -3)
        if highs[-1] < lows[-3]:
            # Calculate gap size as percentage of price
            gap_size = (lows[-3] - highs[-1]) / lows[-3]
            
            # Only consider gaps larger than minimum size
            if gap_size >= self.min_gap_size:
                # Calculate strength based on gap size and volume
                strength = min(1.0, gap_size * 100)  # Normalize to 0-1
                
                # Create bearish FVG
                fvg = FairValueGap(
                    ticker=ticker,
                    timeframe=timeframe,
                    high=lows[-3],
                    low=highs[-1],
                    direction="bearish",
                    strength=strength,
                    created_at=ohlc_data.index[-1].to_pydatetime(),
                    notes=f"Bearish FVG: {gap_size:.2%} gap"
                )
                
                fvgs.append(fvg)
        
        return fvgs
    
    def _update_fvgs(
        self, ticker: str, timeframe: str, new_fvgs: List[FairValueGap], ohlc_data: pd.DataFrame
    ) -> None:
        """Update stored FVGs with new FVGs and increment age of existing FVGs."""
        key = f"{ticker}_{timeframe}"
        
        if key not in self.fvgs:
            self.fvgs[key] = []
        
        # Add new FVGs
        self.fvgs[key].extend(new_fvgs)
        
        # Increment age of existing FVGs
        for fvg in self.fvgs[key]:
            fvg.age_in_bars += 1
        
        # Remove old FVGs
        self.fvgs[key] = [fvg for fvg in self.fvgs[key] if fvg.age_in_bars <= self.max_age]
    
    def _check_filled_fvgs(
        self, ticker: str, timeframe: str, ohlc_data: pd.DataFrame
    ) -> List[FairValueGap]:
        """
        Check if any FVGs have been filled.
        
        This method checks if price has moved into any existing FVGs,
        marking them as filled if so.
        """
        active_fvgs = []
        key = f"{ticker}_{timeframe}"
        
        if key not in self.fvgs:
            return active_fvgs
        
        # Get current price data
        current_price = ohlc_data["close"].iloc[-1]
        current_time = ohlc_data.index[-1].to_pydatetime()
        
        # Check for filled FVGs
        for i, fvg in enumerate(self.fvgs[key]):
            if not fvg.filled:
                # Check if price has moved into the FVG
                if fvg.low <= current_price <= fvg.high:
                    # FVG is being filled
                    self.fvgs[key][i].filled = True
                    self.fvgs[key][i].filled_at = current_time
                    self.fvgs[key][i].filled_price = current_price
                else:
                    # FVG is still active
                    active_fvgs.append(fvg)
        
        return active_fvgs
    
    def _get_fvgs(self, ticker: str, timeframe: str) -> List[FairValueGap]:
        """Get stored FVGs for a ticker and timeframe."""
        key = f"{ticker}_{timeframe}"
        return self.fvgs.get(key, [])
    
    def _generate_analysis(
        self, ticker: str, timeframe: str, active_fvgs: List[FairValueGap]
    ) -> Dict[str, Any]:
        """Generate analysis based on FVGs."""
        analysis = {
            "has_active_fvgs": len(active_fvgs) > 0,
            "fvg_count": len(active_fvgs),
            "strongest_fvg": None,
            "directional_bias": "neutral",
            "notes": []
        }
        
        if active_fvgs:
            # Find strongest FVG
            strongest_fvg = max(active_fvgs, key=lambda x: x.strength)
            analysis["strongest_fvg"] = {
                "direction": strongest_fvg.direction,
                "strength": strongest_fvg.strength,
                "price_range": (strongest_fvg.low, strongest_fvg.high),
                "created_at": strongest_fvg.created_at.isoformat(),
                "age_in_bars": strongest_fvg.age_in_bars,
                "notes": strongest_fvg.notes
            }
            
            # Determine directional bias
            bullish_fvgs = [f for f in active_fvgs if f.direction == "bullish"]
            bearish_fvgs = [f for f in active_fvgs if f.direction == "bearish"]
            
            if bullish_fvgs and not bearish_fvgs:
                analysis["directional_bias"] = "bullish"
                analysis["notes"].append(f"Found {len(bullish_fvgs)} bullish FVGs")
            elif bearish_fvgs and not bullish_fvgs:
                analysis["directional_bias"] = "bearish"
                analysis["notes"].append(f"Found {len(bearish_fvgs)} bearish FVGs")
            elif bullish_fvgs and bearish_fvgs:
                # Compare strength
                bullish_strength = sum(f.strength for f in bullish_fvgs)
                bearish_strength = sum(f.strength for f in bearish_fvgs)
                
                if bullish_strength > bearish_strength * 1.5:
                    analysis["directional_bias"] = "bullish"
                    analysis["notes"].append("Bullish FVGs are significantly stronger")
                elif bearish_strength > bullish_strength * 1.5:
                    analysis["directional_bias"] = "bearish"
                    analysis["notes"].append("Bearish FVGs are significantly stronger")
                else:
                    analysis["directional_bias"] = "mixed"
                    analysis["notes"].append("Mixed signals from bullish and bearish FVGs")
        else:
            analysis["notes"].append("No active FVGs found")
        
        return analysis
    
    def add_confluence(self, ticker: str, timeframe: str, price_level: float, direction: str) -> Tuple[bool, str]:
        """
        Add confluence to a FVG.
        
        This method is called by other agents to add confluence to a FVG
        when they detect a setup at a similar price level.
        
        Returns:
            Tuple[bool, str]: Success flag and message
        """
        key = f"{ticker}_{timeframe}"
        
        if key not in self.fvgs:
            return False, f"No FVGs found for {ticker} on {timeframe} timeframe"
        
        # Find FVGs near the price level
        for i, fvg in enumerate(self.fvgs[key]):
            # Check if price is within or near the FVG
            if (fvg.low * 0.99 <= price_level <= fvg.high * 1.01 and
                fvg.direction == direction):
                # Add confluence
                self.fvgs[key][i].confluence_count += 1
                return True, f"Added confluence to {direction} FVG at {price_level:.2f}"
        
        return False, f"No matching {direction} FVGs found near {price_level:.2f}" 