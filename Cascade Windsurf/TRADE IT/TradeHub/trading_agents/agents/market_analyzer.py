from typing import Any, Dict, List
import yfinance as yf
import pandas as pd
from loguru import logger
from pydantic import BaseModel
from .base_agent import BaseAgent, AgentState

class MarketData(BaseModel):
    """Model for market analysis data."""
    symbol: str
    timeframe: str
    data: pd.DataFrame
    indicators: Dict[str, Any]
    
    model_config = {
        "arbitrary_types_allowed": True
    }

class MarketAnalyzer(BaseAgent):
    """Agent responsible for analyzing market conditions and trends."""
    
    def __init__(self, agent_id: str = "market_analyzer", config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.default_timeframe = config.get("default_timeframe", "1d")
        self.indicators = config.get("indicators", ["SMA", "RSI", "MACD"])
    
    async def validate(self, data: Any) -> bool:
        """Validate market data input."""
        if not isinstance(data, dict):
            logger.error("Input data must be a dictionary")
            return False
        
        required_fields = ["symbol", "timeframe"]
        if not all(field in data for field in required_fields):
            logger.error(f"Missing required fields: {required_fields}")
            return False
        
        return True
    
    async def process(self, data: Dict[str, Any]) -> MarketData:
        """Process market data and calculate indicators."""
        symbol = data["symbol"]
        timeframe = data.get("timeframe", self.default_timeframe)
        
        logger.info(f"Fetching market data for {symbol} with timeframe {timeframe}")
        
        # Fetch market data
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y", interval=timeframe)
        
        # Calculate indicators
        indicators = self._calculate_indicators(df)
        
        return MarketData(
            symbol=symbol,
            timeframe=timeframe,
            data=df,
            indicators=indicators
        )
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate technical indicators."""
        indicators = {}
        
        if "SMA" in self.indicators:
            indicators["SMA_20"] = df["Close"].rolling(window=20).mean()
            indicators["SMA_50"] = df["Close"].rolling(window=50).mean()
        
        if "RSI" in self.indicators:
            delta = df["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators["RSI"] = 100 - (100 / (1 + rs))
        
        if "MACD" in self.indicators:
            exp1 = df["Close"].ewm(span=12, adjust=False).mean()
            exp2 = df["Close"].ewm(span=26, adjust=False).mean()
            indicators["MACD"] = exp1 - exp2
            indicators["Signal"] = indicators["MACD"].ewm(span=9, adjust=False).mean()
        
        return indicators 