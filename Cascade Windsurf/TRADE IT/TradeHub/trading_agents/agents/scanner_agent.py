from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentState

class BreakoutSetup(BaseModel):
    """Model for a breaker block retest setup."""
    ticker: str
    timeframe: str
    datetime: str
    price: float
    direction: int  # 1 for buy, -1 for sell
    strength: float
    breaker_index: int
    fvg_aligned_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScannerResult(BaseModel):
    """Model for scanner results."""
    timestamp: str
    setups: List[BreakoutSetup] = Field(default_factory=list)
    raw_data: Dict[str, Any] = Field(default_factory=dict)

class BreakerBlockScanner:
    def __init__(
        self, 
        lookback_periods: int = 50,
        min_volume_threshold: int = 10000,
        price_rejection_threshold: float = 0.005,
        fvg_threshold: float = 0.003
    ):
        """
        Initialize the scanner with configuration parameters
        
        Parameters:
        lookback_periods (int): Number of periods to look back for patterns
        min_volume_threshold (int): Minimum volume to consider valid
        price_rejection_threshold (float): Minimum price rejection as decimal (e.g., 0.005 = 0.5%)
        fvg_threshold (float): Minimum fair value gap size as decimal (e.g., 0.003 = 0.3%)
        """
        self.lookback_periods = lookback_periods
        self.min_volume_threshold = min_volume_threshold
        self.price_rejection_threshold = price_rejection_threshold
        self.fvg_threshold = fvg_threshold
        logger.info(f"Initialized BreakerBlockScanner with lookback={lookback_periods}, "
                   f"min_volume={min_volume_threshold}, price_rejection={price_rejection_threshold}, "
                   f"fvg_threshold={fvg_threshold}")
            
    def _calculate_body_size(self, data):
        """Calculate the body size of candles"""
        data['body_size'] = abs(data['close'] - data['open'])
        data['body_percent'] = data['body_size'] / (data['high'] - data['low'])
        data['direction'] = np.where(data['close'] > data['open'], 1, -1)  # 1 for bullish, -1 for bearish
        return data
        
    def _calculate_wicks(self, data):
        """Calculate the size of upper and lower wicks"""
        # Upper wick
        data['upper_wick'] = np.where(
            data['direction'] == 1,
            data['high'] - data['close'],
            data['high'] - data['open']
        )
        
        # Lower wick
        data['lower_wick'] = np.where(
            data['direction'] == 1,
            data['open'] - data['low'],
            data['close'] - data['low']
        )
        
        # Calculate wick ratios
        data['has_top_wick'] = data['upper_wick'] > 0
        data['has_bottom_wick'] = data['lower_wick'] > 0
        return data
    
    def find_breaker_blocks(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Find breaker blocks in the provided OHLCV data
        
        Parameters:
        data (pd.DataFrame): DataFrame with OHLCV data
        
        Returns:
        List[Dict[str, Any]]: List of breaker blocks with their properties
        """
        # Make a copy to avoid modifying the original
        df = data.copy()
        
        # Ensure we have the necessary columns
        df = self._calculate_body_size(df)
        df = self._calculate_wicks(df)
        
        breaker_blocks = []
        
        # Look for potential breaker blocks
        for i in range(self.lookback_periods, len(df) - 5):
            # Check for significant volume
            if df.iloc[i]['volume'] < self.min_volume_threshold:
                continue
                
            # Look for strong candles with significant body
            if df.iloc[i]['body_percent'] < 0.6:
                continue
                
            # Check for price rejection
            if df.iloc[i]['direction'] > 0:  # Bullish candle
                # Check for bearish reversal in the next few candles
                for j in range(i + 1, min(i + 10, len(df))):
                    if df.iloc[j]['direction'] < 0 and df.iloc[j]['body_size'] > df.iloc[i]['body_size'] * 0.7:
                        # Price rejection percentage
                        rejection = (df.iloc[i]['high'] - df.iloc[j]['low']) / df.iloc[i]['high']
                        
                        if rejection > self.price_rejection_threshold:
                            # Found a potential breaker block
                            breaker_blocks.append({
                                'start_idx': i,
                                'end_idx': j,
                                'high': df.iloc[i]['high'],
                                'low': df.iloc[j]['low'],
                                'rejection': float(rejection),
                                'direction': -1,  # Bearish breaker
                                'volume': float(df.iloc[i]['volume']),
                                'strength': float(min(rejection * 2, 1.0))
                            })
                            break
            else:  # Bearish candle
                # Check for bullish reversal in the next few candles
                for j in range(i + 1, min(i + 10, len(df))):
                    if df.iloc[j]['direction'] > 0 and df.iloc[j]['body_size'] > df.iloc[i]['body_size'] * 0.7:
                        # Price rejection percentage
                        rejection = (df.iloc[j]['high'] - df.iloc[i]['low']) / df.iloc[i]['low']
                        
                        if rejection > self.price_rejection_threshold:
                            # Found a potential breaker block
                            breaker_blocks.append({
                                'start_idx': i,
                                'end_idx': j,
                                'high': df.iloc[j]['high'],
                                'low': df.iloc[i]['low'],
                                'rejection': float(rejection),
                                'direction': 1,  # Bullish breaker
                                'volume': float(df.iloc[i]['volume']),
                                'strength': float(min(rejection * 2, 1.0))
                            })
                            break
        
        logger.info(f"Found {len(breaker_blocks)} potential breaker blocks")
        return breaker_blocks
    
    def find_fair_value_gaps(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Find fair value gaps (FVGs) in the provided OHLCV data
        
        Parameters:
        data (pd.DataFrame): DataFrame with OHLCV data
        
        Returns:
        List[Dict[str, Any]]: List of FVGs with their properties
        """
        # Make a copy to avoid modifying the original
        df = data.copy()
        
        fair_value_gaps = []
        
        # Find FVGs - need at least 3 candles
        for i in range(1, len(df) - 1):
            # Bullish FVG: Current candle's low > previous candle's high
            if df.iloc[i+1]['low'] > df.iloc[i]['high']:
                gap_size = (df.iloc[i+1]['low'] - df.iloc[i]['high']) / df.iloc[i]['high']
                
                if gap_size > self.fvg_threshold:
                    fair_value_gaps.append({
                        'idx': i,
                        'upper': float(df.iloc[i+1]['low']),
                        'lower': float(df.iloc[i]['high']),
                        'gap_size': float(gap_size),
                        'direction': 1,  # Bullish FVG
                        'filled': False
                    })
            
            # Bearish FVG: Current candle's high < previous candle's low
            elif df.iloc[i+1]['high'] < df.iloc[i]['low']:
                gap_size = (df.iloc[i]['low'] - df.iloc[i+1]['high']) / df.iloc[i]['low']
                
                if gap_size > self.fvg_threshold:
                    fair_value_gaps.append({
                        'idx': i,
                        'upper': float(df.iloc[i]['low']),
                        'lower': float(df.iloc[i+1]['high']),
                        'gap_size': float(gap_size),
                        'direction': -1,  # Bearish FVG
                        'filled': False
                    })
        
        # Check if FVGs have been filled
        for fvg in fair_value_gaps:
            idx = fvg['idx']
            
            # Check candles after the FVG to see if it's been filled
            for j in range(idx + 2, len(df)):
                if fvg['direction'] == 1:  # Bullish FVG
                    if df.iloc[j]['low'] <= fvg['lower']:
                        fvg['filled'] = True
                        fvg['filled_idx'] = j
                        break
                else:  # Bearish FVG
                    if df.iloc[j]['high'] >= fvg['upper']:
                        fvg['filled'] = True
                        fvg['filled_idx'] = j
                        break
        
        logger.info(f"Found {len(fair_value_gaps)} fair value gaps")
        return fair_value_gaps

class ScannerAgent(BaseAgent):
    """Agent for scanning for trading setups."""
    
    def __init__(self, agent_id: str = "scanner_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the scanner agent."""
        super().__init__(agent_id=agent_id, config=config or {})
        self.state = AgentState.READY
    
    async def validate(self, data: Any) -> bool:
        """Validate the input data."""
        if not isinstance(data, dict):
            logger.error("Input data must be a dictionary")
            return False
        
        required_keys = ["tickers", "timeframe"]
        if not all(key in data for key in required_keys):
            logger.error(f"Input data missing required keys: {required_keys}")
            return False
        
        return True
    
    async def process(self, data: Dict[str, Any]) -> ScannerResult:
        """Process the input data and return scanner results."""
        logger.info(f"Processing data for {len(data['tickers'])} tickers")
        
        # This is a placeholder for the actual implementation
        # In a real implementation, this would fetch data and analyze it
        
        result = ScannerResult(
            timestamp=datetime.now().isoformat(),
            setups=[],
            raw_data={}
        )
        
        return result 