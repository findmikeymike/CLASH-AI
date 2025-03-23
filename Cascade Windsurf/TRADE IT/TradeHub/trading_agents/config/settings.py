"""
Configuration settings for the trading agent system.
"""
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Tickers to scan
DEFAULT_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", 
    "TSLA", "NVDA", "JPM", "V", "JNJ",
    "WMT", "PG", "DIS", "NFLX", "INTC",
    "AMD", "BA", "HD", "MCD", "NKE"
]

# Timeframes to scan
TIMEFRAMES = {
    "1m": "1 minute",
    "5m": "5 minutes",
    "15m": "15 minutes",
    "30m": "30 minutes",
    "1h": "1 hour",
    "4h": "4 hours",
    "1d": "1 day",
    "1wk": "1 week"
}

# Scanner settings
SCANNER_SETTINGS = {
    "default_timeframe": "1d",
    "period": "1y",
    "min_strength": 0.3,
    "fvg_aligned_only": True
}

# API keys and credentials (from environment variables)
API_KEYS = {
    "alpha_vantage": os.getenv("ALPHA_VANTAGE_API_KEY", ""),
    "finnhub": os.getenv("FINNHUB_API_KEY", ""),
    "polygon": os.getenv("POLYGON_API_KEY", "")
}

# Prefect settings
PREFECT_SETTINGS = {
    "flow_run_name": "Breaker Block Scanner",
    "schedule_interval": "0 18 * * 1-5",  # 6 PM on weekdays
    "retries": 3,
    "retry_delay_seconds": 60
}

class Settings(BaseModel):
    """Settings for the trading agent system."""
    
    # Ticker and timeframe
    ticker: str = Field(default="AAPL", description="Ticker symbol to scan")
    timeframe: str = Field(default="1d", description="Timeframe to scan")
    period: str = Field(default="1y", description="Period to fetch data for")
    
    # Scanner parameters
    lookback_periods: int = Field(default=50, description="Number of periods to look back")
    min_volume_threshold: int = Field(default=10000, description="Minimum volume threshold")
    price_rejection_threshold: float = Field(default=0.005, description="Price rejection threshold (decimal)")
    fvg_threshold: float = Field(default=0.003, description="Fair value gap threshold (decimal)")
    
    # API settings
    api_key: Optional[str] = Field(default=None, description="API key for data provider")
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True 