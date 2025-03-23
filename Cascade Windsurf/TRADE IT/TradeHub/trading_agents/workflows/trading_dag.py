from prefect import flow, task
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import yfinance as yf
from loguru import logger

from ..agents.scanner_agent import BreakerBlockScanner
from ..config.settings import DEFAULT_TICKERS, SCANNER_SETTINGS, Settings

@task(name="Fetch Market Data")
def fetch_market_data(ticker: str, timeframe: str, period: str = "1y") -> pd.DataFrame:
    """Task for fetching market data."""
    logger.info(f"Fetching data for {ticker} on {timeframe} timeframe")
    
    try:
        data = yf.download(ticker, period=period, interval=timeframe)
        
        # Rename columns to lowercase for consistency
        data.columns = [col.lower() for col in data.columns]
        
        logger.info(f"Fetched {len(data)} data points for {ticker}")
        return data
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {str(e)}")
        raise

@task(name="Scan for Breaker Blocks")
def scan_for_breaker_blocks(
    data: pd.DataFrame,
    settings: Settings
) -> Dict[str, Any]:
    """Task for scanning for breaker blocks and fair value gaps."""
    logger.info(f"Scanning for breaker blocks with lookback of {settings.lookback_periods} periods")
    
    scanner = BreakerBlockScanner(
        lookback_periods=settings.lookback_periods,
        min_volume_threshold=settings.min_volume_threshold,
        price_rejection_threshold=settings.price_rejection_threshold,
        fvg_threshold=settings.fvg_threshold
    )
    
    # Find breaker blocks
    breaker_blocks = scanner.find_breaker_blocks(data)
    logger.info(f"Found {len(breaker_blocks)} breaker blocks")
    
    # Find fair value gaps
    fair_value_gaps = scanner.find_fair_value_gaps(data)
    logger.info(f"Found {len(fair_value_gaps)} fair value gaps")
    
    return {
        "data": data,
        "breaker_blocks": breaker_blocks,
        "fair_value_gaps": fair_value_gaps,
        "timestamp": datetime.now().isoformat()
    }

@flow(name="Trading Workflow")
def trading_workflow(
    settings: Optional[Settings] = None
) -> Dict[str, Any]:
    """Main trading workflow that orchestrates all agents."""
    if settings is None:
        settings = Settings()
    
    logger.info(f"Starting trading workflow for {settings.ticker} on {settings.timeframe} timeframe")
    
    # Step 1: Fetch market data
    data = fetch_market_data(
        ticker=settings.ticker,
        timeframe=settings.timeframe,
        period=settings.period
    )
    
    # Step 2: Scan for breaker blocks and fair value gaps
    scan_results = scan_for_breaker_blocks(
        data=data,
        settings=settings
    )
    
    logger.info("Breaker block scan completed")
    
    # TODO: Add more tasks for other agents in the workflow
    # - Technical Analysis
    # - Risk Management
    # - Trade Execution
    
    return scan_results

if __name__ == "__main__":
    # Run the workflow with default settings
    trading_workflow() 