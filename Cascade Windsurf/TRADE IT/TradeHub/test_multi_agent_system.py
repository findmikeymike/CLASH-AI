#!/usr/bin/env python
"""
Test script for the multi-agent trading system.
This script demonstrates how the various agents work together to analyze market data,
detect setups, and make trading decisions.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger
import matplotlib.pyplot as plt
import seaborn as sns

from trading_agents.agents import (
    CoordinatorAgent, BreakerBlockAgent, FVGAgent, 
    OrderFlowAgent, OptionsExpertAgent, DecisionAgent,
    MarketAnalyzerAgent
)

# Configure logging
logger.remove()
logger.add("logs/test_multi_agent.log", rotation="500 MB", level="INFO")
logger.add(lambda msg: print(msg), level="INFO")

def generate_sample_ohlc_data(ticker: str, periods: int = 100) -> pd.DataFrame:
    """Generate sample OHLC data for testing."""
    np.random.seed(42)  # For reproducibility
    
    # Start with a base price
    base_price = 100.0
    
    # Generate random price movements
    returns = np.random.normal(0, 0.01, periods)
    price_multipliers = np.cumprod(1 + returns)
    
    # Generate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=periods)
    dates = pd.date_range(start=start_date, end=end_date, periods=periods)
    
    # Generate OHLC data
    data = []
    for i, date in enumerate(dates):
        price = base_price * price_multipliers[i]
        
        # Add some randomness to open, high, low
        open_price = price * (1 + np.random.normal(0, 0.003))
        high_price = max(open_price, price) * (1 + abs(np.random.normal(0, 0.005)))
        low_price = min(open_price, price) * (1 - abs(np.random.normal(0, 0.005)))
        
        # Ensure high is highest and low is lowest
        high_price = max(high_price, open_price, price)
        low_price = min(low_price, open_price, price)
        
        # Generate volume
        volume = int(np.random.exponential(100000))
        
        data.append({
            'date': date,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': price,
            'volume': volume
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)
    
    # Add a gap for testing FVG detection
    if periods > 20:
        # Create a bullish FVG around index 30 (or at index periods//3 if periods < 30)
        fvg_index = min(30, periods // 3)
        if fvg_index > 2:
            df.iloc[fvg_index, df.columns.get_loc('low')] = df.iloc[fvg_index-2, df.columns.get_loc('high')] * 1.02
        
        # Create a bearish FVG around index 60 (or at index 2*periods//3 if periods < 60)
        fvg_index = min(60, 2 * periods // 3)
        if fvg_index > 2:
            df.iloc[fvg_index, df.columns.get_loc('high')] = df.iloc[fvg_index-2, df.columns.get_loc('low')] * 0.98
    
    # Add a support/resistance level for testing breaker blocks
    if periods > 40:
        # Create a resistance level around index 40-45 (or at the middle of the data if periods < 40)
        res_start = min(40, periods // 2)
        res_end = min(45, res_start + 5)
        
        if res_end > res_start:
            resistance_level = df.iloc[res_start:res_end, df.columns.get_loc('high')].mean()
            for i in range(res_start, res_end):
                df.iloc[i, df.columns.get_loc('high')] = resistance_level * (1 + np.random.normal(0, 0.002))
            
            # Break the resistance around index 50 (or near the end if periods < 50)
            break_index = min(50, int(periods * 0.8))
            if break_index > res_end:
                for i in range(break_index, min(break_index + 5, periods)):
                    df.iloc[i, df.columns.get_loc('close')] = resistance_level * 1.05
    
    return df

# Create mock result classes for testing
class BreakerBlockResult:
    def __init__(self, ticker, timeframe):
        self.active_retests = []
        # Add a sample retest
        self.active_retests.append(type('BreakerRetest', (), {
            'high': 105.0,
            'low': 103.0,
            'direction': 'bullish',
            'strength': 0.8,
            'confluence_count': 2,
            'notes': 'Strong bullish breaker block retest'
        }))

class FVGResult:
    def __init__(self, ticker, timeframe):
        self.active_fvgs = []
        # Add a sample FVG
        self.active_fvgs.append(type('FVG', (), {
            'high': 102.0,
            'low': 100.0,
            'direction': 'bullish',
            'strength': 0.75,
            'confluence_count': 1,
            'age_in_bars': 3,
            'notes': 'Recent bullish fair value gap'
        }))

class OptionsResult:
    def __init__(self, ticker):
        self.analysis = {
            'overall_bias': {
                'direction': 'bullish',
                'strength': 0.85
            },
            'notes': 'Strong call buying activity'
        }
        self.call_put_ratio = 2.5
        self.iv_percentile = 65
        self.signals = [
            type('OptionsSignal', (), {
                'strike': 105.0,
                'expiry': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'type': 'call',
                'volume': 5000,
                'open_interest': 15000
            })
        ]

async def test_multi_agent_system():
    """Test the multi-agent trading system."""
    logger.info("Starting multi-agent system test")
    
    # Initialize agents
    coordinator = CoordinatorAgent()
    
    # Mock the agent run methods to return test data
    async def mock_breaker_agent_run(data):
        return {
            "success": True,
            "result": BreakerBlockResult(data["ticker"], data["timeframe"])
        }
    
    async def mock_fvg_agent_run(data):
        return {
            "success": True,
            "result": FVGResult(data["ticker"], data["timeframe"])
        }
    
    async def mock_options_agent_run(data):
        return {
            "success": True,
            "result": OptionsResult(data["ticker"])
        }
    
    async def mock_market_analyzer_run(data):
        return {
            "success": True,
            "result": {
                "market_analysis": {
                    "stance": "bullish",
                    "score": 5.2,
                    "regime": "trending_bullish",
                    "warnings": [],
                    "trend_analysis": {
                        "SPY": "bullish",
                        "QQQ": "bullish",
                        "IWM": "neutral",
                        "DIA": "bullish"
                    },
                    "options_analysis": {
                        "SPY": "bullish",
                        "QQQ": "bullish"
                    },
                    "gex": {
                        "SPY": 1.5e6,
                        "QQQ": 2.1e6
                    },
                    "regimes": {
                        "SPY": "trending_bullish",
                        "QQQ": "trending_bullish",
                        "IWM": "early_trend",
                        "DIA": "trending_bullish"
                    },
                    "yield_curve": "normal"
                },
                "sector_analysis": {
                    "leading_sectors": ["XLK", "XLF", "XLY"],
                    "lagging_sectors": ["XLU", "XLP", "XLRE"],
                    "sector_performance": {
                        "XLK": {"status": "leading", "strength": 0.85, "momentum": "increasing"},
                        "XLF": {"status": "leading", "strength": 0.75, "momentum": "stable"},
                        "XLY": {"status": "leading", "strength": 0.70, "momentum": "increasing"},
                        "XLI": {"status": "neutral", "strength": 0.50, "momentum": "stable"},
                        "XLV": {"status": "neutral", "strength": 0.45, "momentum": "decreasing"},
                        "XLE": {"status": "neutral", "strength": 0.55, "momentum": "increasing"},
                        "XLB": {"status": "neutral", "strength": 0.50, "momentum": "stable"},
                        "XLU": {"status": "lagging", "strength": 0.30, "momentum": "decreasing"},
                        "XLP": {"status": "lagging", "strength": 0.35, "momentum": "stable"},
                        "XLRE": {"status": "lagging", "strength": 0.25, "momentum": "decreasing"}
                    },
                    "rotation_signals": {
                        "XLK": "rotating_in",
                        "XLF": "stable",
                        "XLY": "rotating_in",
                        "XLI": "stable",
                        "XLV": "rotating_out",
                        "XLE": "rotating_in",
                        "XLB": "stable",
                        "XLU": "rotating_out",
                        "XLP": "stable",
                        "XLRE": "rotating_out"
                    }
                }
            }
        }
    
    # Replace the actual agent run methods with our mocks
    coordinator.agents["breaker_block_agent"].run = mock_breaker_agent_run
    coordinator.agents["fvg_agent"].run = mock_fvg_agent_run
    coordinator.agents["options_agent"].run = mock_options_agent_run
    coordinator.agents["market_analyzer"].run = mock_market_analyzer_run
    
    # Generate sample data
    ticker = "AAPL"
    timeframes = ["1h", "4h"]
    
    # Create OHLC data for each timeframe
    ohlc_data = {}
    for tf in timeframes:
        periods = 100 if tf == "1h" else 50
        ohlc_data[tf] = generate_sample_ohlc_data(ticker, periods=periods)
    
    logger.info(f"Generated sample data for {ticker} on {', '.join(timeframes)} timeframes")
    
    # Process data through the coordinator
    input_data = {
        "tickers": [ticker],
        "timeframes": timeframes,
        "ohlc_data": {ticker: ohlc_data}
    }
    
    result = await coordinator.process(input_data)
    
    # Display results
    logger.info(f"Multi-agent pipeline completed")
    logger.info(f"Found {len(result['setups'])} setups and {len(result['confluences'])} confluences")
    
    # Display market analysis
    if 'market_analysis' in result:
        logger.info("\nMarket Analysis:")
        logger.info(f"Market Stance: {result['market_analysis'].get('stance', 'unknown')}")
        logger.info(f"Market Score: {result['market_analysis'].get('score', 0)}")
        
        # Log market regime information
        logger.info(f"Market Regime: {result['market_analysis'].get('regime', 'unknown')}")
        
        # Log any market warnings
        warnings = result['market_analysis'].get('warnings', [])
        if warnings:
            logger.info("\nMarket Warnings:")
            for warning in warnings:
                logger.info(f"- {warning}")
    
    # Display sector analysis
    if 'sector_analysis' in result:
        logger.info("\nSector Analysis:")
        logger.info(f"Leading Sectors: {', '.join(result['sector_analysis'].get('leading_sectors', []))}")
        logger.info(f"Lagging Sectors: {', '.join(result['sector_analysis'].get('lagging_sectors', []))}")
    
    # Display setups
    for i, setup in enumerate(result['setups']):
        logger.info(f"\nSetup {i+1}:")
        logger.info(f"Type: {setup.setup_type}")
        logger.info(f"Ticker: {setup.ticker}")
        logger.info(f"Timeframe: {setup.timeframe}")
        logger.info(f"Direction: {'Bullish' if setup.direction > 0 else 'Bearish'}")
        logger.info(f"Entry Price: {setup.entry_price:.2f}")
        logger.info(f"Stop Loss: {setup.stop_loss:.2f}")
        logger.info(f"Take Profit: {setup.take_profit:.2f}")
        logger.info(f"Confidence: {setup.confidence:.2f}")
        
        # Display market context if available
        if hasattr(setup, 'market_context'):
            logger.info("\nMarket Context:")
            if 'market_stance' in setup.market_context:
                logger.info(f"Market Stance: {setup.market_context['market_stance']}")
            if 'market_regime' in setup.market_context:
                logger.info(f"Market Regime: {setup.market_context['market_regime']}")
            if 'tags' in setup.market_context and setup.market_context['tags']:
                logger.info(f"Context Tags: {', '.join(setup.market_context['tags'])}")
            if 'warnings' in setup.market_context and setup.market_context['warnings']:
                logger.info(f"Warnings: {', '.join(setup.market_context['warnings'])}")
        
        # Display analysis details
        if hasattr(setup, 'analysis') and setup.analysis:
            logger.info("\nAnalysis Details:")
            for key, value in setup.analysis.items():
                logger.info(f"  {key}: {value}")
    
    # Display confluences
    for i, confluence in enumerate(result['confluences']):
        logger.info(f"\nConfluence {i+1}:")
        logger.info(f"Ticker: {confluence.get('ticker', '')}")
        logger.info(f"Direction: {confluence.get('direction', '')}")
        logger.info(f"Price Level: {confluence.get('price_level', 0):.2f}")
        logger.info(f"Strength: {confluence.get('strength', 0):.2f}")
        logger.info(f"Timeframes: {', '.join(confluence.get('timeframes', []))}")
        logger.info(f"Setup Types: {', '.join(confluence.get('setup_types', []))}")
    
    # Display trade recommendations
    for i, recommendation in enumerate(result['trade_recommendations']):
        logger.info(f"\nTrade Recommendation {i+1}:")
        logger.info(f"Ticker: {recommendation.get('ticker', '')}")
        logger.info(f"Direction: {recommendation.get('direction', '')}")
        logger.info(f"Entry Price: {recommendation.get('entry_price', 0):.2f}")
        logger.info(f"Stop Loss: {recommendation.get('stop_loss', 0):.2f}")
        logger.info(f"Take Profit: {recommendation.get('take_profit', 0):.2f}")
        logger.info(f"Confidence: {recommendation.get('confidence', 0):.2f}")
        logger.info(f"Risk-Reward: {recommendation.get('risk_reward', 0):.2f}")
        logger.info(f"Source: {recommendation.get('source', '')}")
        
        # Display market context if available
        if 'market_context' in recommendation:
            logger.info(f"Market Context: {recommendation['market_context'].get('tag', 'Unknown')}")
    
    # Save a chart for visualization
    plt.figure(figsize=(12, 8))
    
    # Plot OHLC data
    ax1 = plt.subplot(2, 1, 1)
    ohlc_df = ohlc_data['1h']
    ax1.plot(ohlc_df.index, ohlc_df['close'], label='Close Price')
    
    # Mark setups on the chart
    for setup in result['setups']:
        if setup.timeframe == '1h':
            marker = '^' if setup.direction > 0 else 'v'
            color = 'g' if setup.direction > 0 else 'r'
            ax1.scatter(ohlc_df.index[-1], setup.entry_price, marker=marker, color=color, s=100)
    
    ax1.set_title(f"{ticker} Price Chart with Trading Setups")
    ax1.legend()
    
    # Plot volume
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    ax2.bar(ohlc_df.index, ohlc_df['volume'], color='blue', alpha=0.5)
    ax2.set_title(f"{ticker} Volume")
    
    plt.tight_layout()
    plt.savefig(f"{ticker}_analysis.png")
    logger.info(f"Saved chart as {ticker}_analysis.png")
    
    return result

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_multi_agent_system()) 