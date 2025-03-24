"""
Breaker Block Agent - Scans for breaker block setups and retests.
This agent identifies breaker blocks (former support/resistance areas) and
detects when price returns to test these levels.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel
import sys
from scipy.signal import argrelextrema

from .base_agent import BaseAgent, AgentState

# Configure enhanced logging - "nuclear logging" approach
logger.remove()  # Remove default handler
logger.add(sys.stderr, level="INFO")
logger.add("logs/breaker_block_{time}.log", rotation="500 MB", level="DEBUG", 
           format="{time} | {level} | {message} | {extra}")

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
    entry_zone: Optional[float] = None
    fvg_high: Optional[float] = None
    fvg_low: Optional[float] = None
    sweep_level: Optional[float] = None
    imbalance_type: Optional[str] = None  # "FVG" or "BPR"
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

class BreakerBlockSetupDetector:
    """
    ICT Breaker Block Setup Detector for integration with IBKR app
    
    The Breaker Block setup is characterized by:
    1. Price sweeps a liquidity level (swing point)
    2. Creates a Breaker Block / COS in the opposite direction
    3. Creates a Fair Value Gap or BPR during the reversal
    4. Signal is generated when price retraces to the FVG/BPR
    
    Monitors multiple timeframes: 15m, 30m, 1h, 4h for multiple tickers
    """
    
    def __init__(self, timeframes=None):
        """
        Initialize the detector with configurable timeframes
        
        Parameters:
        -----------
        timeframes : list
            List of timeframes to analyze (e.g., ['15m', '30m', '1h', '4h'])
        """
        # Set default timeframes if none provided
        if timeframes is None:
            self.timeframes = ['15m', '30m', '1h', '4h']
        else:
            self.timeframes = timeframes
        
        # Store data, setups, and signals for each ticker and timeframe
        self.data = {}
        self.breaker_setups = {}
        self.active_signals = {}
        
        # Configure logging
        logger.info("Breaker Block Detector initialized")
    
    def initialize_ticker(self, ticker):
        """
        Initialize data structures for a new ticker
        
        Parameters:
        -----------
        ticker : str
            Ticker symbol (e.g., 'AAPL', 'SPY')
        """
        if ticker not in self.data:
            self.data[ticker] = {}
            self.breaker_setups[ticker] = {}
            self.active_signals[ticker] = {}
            
            for tf in self.timeframes:
                self.data[ticker][tf] = None
                self.breaker_setups[ticker][tf] = []
                self.active_signals[ticker][tf] = []
            
            logger.info(f"Initialized ticker: {ticker}")
    
    def process_data(self, ticker, timeframe, df):
        """
        Process new data for a specific ticker and timeframe
        
        Parameters:
        -----------
        ticker : str
            Ticker symbol (e.g., 'AAPL', 'SPY')
        timeframe : str
            Timeframe to analyze (e.g., '15m', '1h', '4h')
        df : pandas.DataFrame
            OHLCV data with datetime index
        
        Returns:
        --------
        tuple
            (DataFrame with analysis, List of setups, List of signals)
        """
        # Initialize ticker if not already done
        self.initialize_ticker(ticker)
        
        try:
            # Store the data
            self.data[ticker][timeframe] = df
            
            # Check if we have enough data
            if len(df) < 50:
                logger.warning(f"Insufficient data for {ticker} on {timeframe} timeframe")
                return None, [], []
            
            # Perform analysis
            df = self.identify_swing_liquidity(df)
            df = self.identify_liquidity_sweeps_from_swings(df)
            df = self.identify_fvg_bpr(df)
            df = self.identify_breaker_blocks(df)
            
            # Detect complete setups
            setups = self.detect_complete_setups(df)
            self.breaker_setups[ticker][timeframe] = setups
            
            # Check for active signals (retests of FVG/BPR)
            active_signals = self.check_for_retests(df, setups)
            self.active_signals[ticker][timeframe] = active_signals
            
            # Log results
            logger.info(f"Found {len(setups)} breaker block setups for {ticker} on {timeframe}")
            if active_signals:
                logger.info(f"Currently {len(active_signals)} active signals for {ticker} on {timeframe}")
            
            return df, setups, active_signals
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker} on {timeframe}: {str(e)}")
            return None, [], []
    
    def identify_swing_liquidity(self, df, window=5):
        """
        Identify significant swing points that can act as liquidity levels
        
        Parameters:
        -----------
        df : pandas.DataFrame
            OHLCV data
        window : int
            Window size for identifying swing points
            
        Returns:
        --------
        DataFrame with swing liquidity levels identified
        """
        # Create copy of dataframe
        result = df.copy()
        
        # Add columns for swing liquidity levels
        result['swing_high_liquidity'] = False
        result['swing_low_liquidity'] = False
        result['swing_high_level'] = np.nan
        result['swing_low_level'] = np.nan
        
        # Identify swing highs and lows
        high_idx = argrelextrema(result['high'].values, np.greater, order=window)[0]
        low_idx = argrelextrema(result['low'].values, np.less, order=window)[0]
        
        # Mark swing highs
        for idx in high_idx:
            result.iloc[idx, result.columns.get_loc('swing_high_liquidity')] = True
            result.iloc[idx, result.columns.get_loc('swing_high_level')] = result.iloc[idx]['high']
        
        # Mark swing lows
        for idx in low_idx:
            result.iloc[idx, result.columns.get_loc('swing_low_liquidity')] = True
            result.iloc[idx, result.columns.get_loc('swing_low_level')] = result.iloc[idx]['low']
        
        return result
    
    def identify_liquidity_sweeps_from_swings(self, df, n_candles=3):
        """
        Identify liquidity sweeps based on swing points
        
        Parameters:
        -----------
        df : pandas.DataFrame
            OHLCV data with swing liquidity levels identified
        n_candles : int
            Number of candles to check after liquidity level is hit
            
        Returns:
        --------
        DataFrame with liquidity sweeps identified
        """
        # Create copy of dataframe
        result = df.copy()
        
        # Add columns for liquidity sweeps
        result['high_sweep'] = False
        result['low_sweep'] = False
        result['high_sweep_level'] = np.nan
        result['low_sweep_level'] = np.nan
        
        # Process swing high levels
        for i in range(len(result)):
            if result.iloc[i]['swing_high_liquidity']:
                level = result.iloc[i]['swing_high_level']
                
                # Look for price exceeding this level in future candles
                for j in range(i+1, min(i+20, len(result) - n_candles)):
                    # Check if price exceeds swing high
                    if result.iloc[j]['high'] > level:
                        # Check if price quickly reverses (within n_candles)
                        if result.iloc[j:j+n_candles+1]['low'].min() < level:
                            result.iloc[j, result.columns.get_loc('high_sweep')] = True
                            result.iloc[j, result.columns.get_loc('high_sweep_level')] = level
                            break
        
        # Process swing low levels
        for i in range(len(result)):
            if result.iloc[i]['swing_low_liquidity']:
                level = result.iloc[i]['swing_low_level']
                
                # Look for price exceeding this level in future candles
                for j in range(i+1, min(i+20, len(result) - n_candles)):
                    # Check if price exceeds swing low
                    if result.iloc[j]['low'] < level:
                        # Check if price quickly reverses (within n_candles)
                        if result.iloc[j:j+n_candles+1]['high'].max() > level:
                            result.iloc[j, result.columns.get_loc('low_sweep')] = True
                            result.iloc[j, result.columns.get_loc('low_sweep_level')] = level
                            break
        
        return result
    
    def identify_fvg_bpr(self, df):
        """
        Identify Fair Value Gaps (FVG) and Bullish/Bearish Premium Raids (BPR)
        
        Parameters:
        -----------
        df : pandas.DataFrame
            OHLCV data
        
        Returns:
        --------
        DataFrame with FVG and BPR identified
        """
        # Create copy of dataframe
        result = df.copy()
        
        # Add columns for FVG and BPR
        result['bullish_fvg'] = False
        result['bearish_fvg'] = False
        result['bullish_bpr'] = False
        result['bearish_bpr'] = False
        result['bullish_fvg_low'] = np.nan
        result['bullish_fvg_high'] = np.nan
        result['bearish_fvg_low'] = np.nan
        result['bearish_fvg_high'] = np.nan
        result['bullish_bpr_level'] = np.nan
        result['bearish_bpr_level'] = np.nan
        
        # Identify Bullish FVG (current candle's low > previous candle's high)
        for i in range(1, len(result) - 1):
            if result.iloc[i+1]['low'] > result.iloc[i-1]['high']:
                result.iloc[i, result.columns.get_loc('bullish_fvg')] = True
                result.iloc[i, result.columns.get_loc('bullish_fvg_low')] = result.iloc[i-1]['high']
                result.iloc[i, result.columns.get_loc('bullish_fvg_high')] = result.iloc[i+1]['low']
        
        # Identify Bearish FVG (current candle's high < previous candle's low)
        for i in range(1, len(result) - 1):
            if result.iloc[i+1]['high'] < result.iloc[i-1]['low']:
                result.iloc[i, result.columns.get_loc('bearish_fvg')] = True
                result.iloc[i, result.columns.get_loc('bearish_fvg_high')] = result.iloc[i-1]['low']
                result.iloc[i, result.columns.get_loc('bearish_fvg_low')] = result.iloc[i+1]['high']
        
        # Identify Bullish BPR (bullish momentum after low sweep)
        for i in range(len(result) - 2):
            if result.iloc[i]['low_sweep']:
                level = result.iloc[i]['low_sweep_level']
                
                # Check for strong bullish candle after sweep
                if (result.iloc[i+1]['close'] > result.iloc[i+1]['open'] and 
                    (result.iloc[i+1]['close'] - result.iloc[i+1]['open']) / 
                    (result.iloc[i+1]['high'] - result.iloc[i+1]['low']) > 0.5):  # Body is 50% of range
                    
                    result.iloc[i+1, result.columns.get_loc('bullish_bpr')] = True
                    result.iloc[i+1, result.columns.get_loc('bullish_bpr_level')] = level
        
        # Identify Bearish BPR (bearish momentum after high sweep)
        for i in range(len(result) - 2):
            if result.iloc[i]['high_sweep']:
                level = result.iloc[i]['high_sweep_level']
                
                # Check for strong bearish candle after sweep
                if (result.iloc[i+1]['close'] < result.iloc[i+1]['open'] and 
                    (result.iloc[i+1]['open'] - result.iloc[i+1]['close']) / 
                    (result.iloc[i+1]['high'] - result.iloc[i+1]['low']) > 0.5):  # Body is 50% of range
                    
                    result.iloc[i+1, result.columns.get_loc('bearish_bpr')] = True
                    result.iloc[i+1, result.columns.get_loc('bearish_bpr_level')] = level
        
        return result
    
    def identify_breaker_blocks(self, df):
        """
        Identify potential breaker blocks
        
        Parameters:
        -----------
        df : pandas.DataFrame
            OHLCV data with liquidity sweeps and FVG/BPR identified
        
        Returns:
        --------
        DataFrame with breaker blocks identified
        """
        # Create copy of dataframe
        result = df.copy()
        
        # Add columns for breaker blocks
        result['bullish_breaker'] = False
        result['bearish_breaker'] = False
        result['bullish_breaker_low'] = np.nan
        result['bullish_breaker_high'] = np.nan
        result['bearish_breaker_low'] = np.nan
        result['bearish_breaker_high'] = np.nan
        
        # Identify Bullish Breaker Blocks (after low sweep followed by bullish FVG or BPR)
        for i in range(len(result) - 3):
            if result.iloc[i]['low_sweep']:
                # Check for bullish FVG or BPR within next 3 candles
                for j in range(i+1, min(i+4, len(result))):
                    if result.iloc[j]['bullish_fvg'] or result.iloc[j]['bullish_bpr']:
                        # The last bearish candle before the FVG/BPR is the breaker block
                        for k in range(j-1, i-1, -1):
                            if result.iloc[k]['close'] < result.iloc[k]['open']:  # Bearish candle
                                result.iloc[k, result.columns.get_loc('bullish_breaker')] = True
                                result.iloc[k, result.columns.get_loc('bullish_breaker_low')] = result.iloc[k]['low']
                                result.iloc[k, result.columns.get_loc('bullish_breaker_high')] = result.iloc[k]['high']
                                break
                        break
        
        # Identify Bearish Breaker Blocks (after high sweep followed by bearish FVG or BPR)
        for i in range(len(result) - 3):
            if result.iloc[i]['high_sweep']:
                # Check for bearish FVG or BPR within next 3 candles
                for j in range(i+1, min(i+4, len(result))):
                    if result.iloc[j]['bearish_fvg'] or result.iloc[j]['bearish_bpr']:
                        # The last bullish candle before the FVG/BPR is the breaker block
                        for k in range(j-1, i-1, -1):
                            if result.iloc[k]['close'] > result.iloc[k]['open']:  # Bullish candle
                                result.iloc[k, result.columns.get_loc('bearish_breaker')] = True
                                result.iloc[k, result.columns.get_loc('bearish_breaker_low')] = result.iloc[k]['low']
                                result.iloc[k, result.columns.get_loc('bearish_breaker_high')] = result.iloc[k]['high']
                                break
                        break
        
        return result
    
    def detect_complete_setups(self, df):
        """
        Detect complete breaker block setups
        
        Parameters:
        -----------
        df : pandas.DataFrame
            OHLCV data with all elements identified
        
        Returns:
        --------
        List of complete breaker block setups
        """
        setups = []
        
        # Detect Bullish Breaker Block Setups
        for i in range(len(df) - 1):
            if df.iloc[i]['bullish_breaker']:
                # Extract the liquidity sweep, FVG/BPR, and breaker block details
                sweep_idx = None
                fvg_bpr_idx = None
                
                # Look back for the liquidity sweep
                for j in range(i-1, max(0, i-5), -1):
                    if df.iloc[j]['low_sweep']:
                        sweep_idx = j
                        break
                
                # Look forward for the FVG or BPR
                for j in range(i+1, min(i+5, len(df))):
                    if df.iloc[j]['bullish_fvg'] or df.iloc[j]['bullish_bpr']:
                        fvg_bpr_idx = j
                        break
                
                if sweep_idx is not None and fvg_bpr_idx is not None:
                    # Define the setup
                    setup = {
                        'type': 'bullish',
                        'sweep_idx': sweep_idx,
                        'breaker_idx': i,
                        'fvg_bpr_idx': fvg_bpr_idx,
                        'sweep_level': df.iloc[sweep_idx]['low_sweep_level'],
                        'breaker_low': df.iloc[i]['bullish_breaker_low'],
                        'breaker_high': df.iloc[i]['bullish_breaker_high']
                    }
                    
                    # Add FVG or BPR details
                    if df.iloc[fvg_bpr_idx]['bullish_fvg']:
                        setup['imbalance_type'] = 'FVG'
                        setup['imbalance_low'] = df.iloc[fvg_bpr_idx]['bullish_fvg_low']
                        setup['imbalance_high'] = df.iloc[fvg_bpr_idx]['bullish_fvg_high']
                    else:
                        setup['imbalance_type'] = 'BPR'
                        setup['imbalance_level'] = df.iloc[fvg_bpr_idx]['bullish_bpr_level']
                        setup['imbalance_low'] = df.iloc[fvg_bpr_idx]['bullish_bpr_level'] * 0.999  # Approx
                        setup['imbalance_high'] = df.iloc[fvg_bpr_idx]['bullish_bpr_level'] * 1.001  # Approx
                    
                    # Add timestamp info for each key point
                    setup['sweep_time'] = df.index[sweep_idx]
                    setup['breaker_time'] = df.index[i]
                    setup['fvg_bpr_time'] = df.index[fvg_bpr_idx]
                    
                    setups.append(setup)
        
        # Detect Bearish Breaker Block Setups
        for i in range(len(df) - 1):
            if df.iloc[i]['bearish_breaker']:
                # Extract the liquidity sweep, FVG/BPR, and breaker block details
                sweep_idx = None
                fvg_bpr_idx = None
                
                # Look back for the liquidity sweep
                for j in range(i-1, max(0, i-5), -1):
                    if df.iloc[j]['high_sweep']:
                        sweep_idx = j
                        break
                
                # Look forward for the FVG or BPR
                for j in range(i+1, min(i+5, len(df))):
                    if df.iloc[j]['bearish_fvg'] or df.iloc[j]['bearish_bpr']:
                        fvg_bpr_idx = j
                        break
                
                if sweep_idx is not None and fvg_bpr_idx is not None:
                    # Define the setup
                    setup = {
                        'type': 'bearish',
                        'sweep_idx': sweep_idx,
                        'breaker_idx': i,
                        'fvg_bpr_idx': fvg_bpr_idx,
                        'sweep_level': df.iloc[sweep_idx]['high_sweep_level'],
                        'breaker_low': df.iloc[i]['bearish_breaker_low'],
                        'breaker_high': df.iloc[i]['bearish_breaker_high']
                    }
                    
                    # Add FVG or BPR details
                    if df.iloc[fvg_bpr_idx]['bearish_fvg']:
                        setup['imbalance_type'] = 'FVG'
                        setup['imbalance_low'] = df.iloc[fvg_bpr_idx]['bearish_fvg_low']
                        setup['imbalance_high'] = df.iloc[fvg_bpr_idx]['bearish_fvg_high']
                    else:
                        setup['imbalance_type'] = 'BPR'
                        setup['imbalance_level'] = df.iloc[fvg_bpr_idx]['bearish_bpr_level']
                        setup['imbalance_low'] = df.iloc[fvg_bpr_idx]['bearish_bpr_level'] * 0.999  # Approx
                        setup['imbalance_high'] = df.iloc[fvg_bpr_idx]['bearish_bpr_level'] * 1.001  # Approx
                    
                    # Add timestamp info for each key point
                    setup['sweep_time'] = df.index[sweep_idx]
                    setup['breaker_time'] = df.index[i]
                    setup['fvg_bpr_time'] = df.index[fvg_bpr_idx]
                    
                    setups.append(setup)
        
        return setups
    
    def check_for_retests(self, df, setups):
        """
        Check for retests of FVG/BPR areas
        
        Parameters:
        -----------
        df : pandas.DataFrame
            OHLCV data
        setups : list
            List of detected setups
        
        Returns:
        --------
        List of active signals (setups that are being retested)
        """
        active_signals = []
        
        for setup in setups:
            # Skip setups that are in the last 5 candles (too recent to be retested)
            if setup['fvg_bpr_idx'] > len(df) - 5:
                continue
            
            # Check if price is currently retesting the FVG/BPR area
            current_price = df.iloc[-1]['close']
            current_time = df.index[-1]
            
            if setup['type'] == 'bullish':
                # For bullish setups, we want price to pullback to the FVG/BPR area
                if (current_price >= setup['imbalance_low'] and 
                    current_price <= setup['imbalance_high']):
                    
                    # Create the signal
                    signal = setup.copy()
                    signal['signal_time'] = current_time
                    signal['entry_price'] = current_price
                    signal['stop_price'] = setup['breaker_low'] * 0.998  # Slightly below breaker block
                    
                    # Target is at least 1:2 risk-reward or next significant resistance
                    risk = current_price - signal['stop_price']
                    signal['target_price'] = current_price + (risk * 2)
                    
                    # Calculate trade metrics
                    signal['risk_amount'] = risk
                    signal['reward_amount'] = signal['target_price'] - current_price
                    signal['risk_reward_ratio'] = signal['reward_amount'] / signal['risk_amount']
                    
                    active_signals.append(signal)
            
            elif setup['type'] == 'bearish':
                # For bearish setups, we want price to pullback to the FVG/BPR area
                if (current_price >= setup['imbalance_low'] and 
                    current_price <= setup['imbalance_high']):
                    
                    # Create the signal
                    signal = setup.copy()
                    signal['signal_time'] = current_time
                    signal['entry_price'] = current_price
                    signal['stop_price'] = setup['breaker_high'] * 1.002  # Slightly above breaker block
                    
                    # Target is at least 1:2 risk-reward or next significant support
                    risk = signal['stop_price'] - current_price
                    signal['target_price'] = current_price - (risk * 2)
                    
                    # Calculate trade metrics
                    signal['risk_amount'] = risk
                    signal['reward_amount'] = current_price - signal['target_price']
                    signal['risk_reward_ratio'] = signal['reward_amount'] / signal['risk_amount']
                    
                    active_signals.append(signal)
        
        return active_signals
    
    def get_all_active_signals(self):
        """
        Get all active signals across all tickers and timeframes
        
        Returns:
        --------
        List of active signals with ticker and timeframe info
        """
        all_signals = []
        
        for ticker in self.active_signals:
            for tf in self.active_signals[ticker]:
                for signal in self.active_signals[ticker][tf]:
                    # Add ticker and timeframe to signal dict
                    enriched_signal = signal.copy()
                    enriched_signal['ticker'] = ticker
                    enriched_signal['timeframe'] = tf
                    
                    all_signals.append(enriched_signal)
        
        return all_signals
    
    def plot_setup(self, ticker, timeframe, setup_idx=0, window=50):
        """
        Plot a specific breaker block setup
        
        Parameters:
        -----------
        ticker : str
            Ticker symbol
        timeframe : str
            Timeframe of the setup
        setup_idx : int
            Index of the setup to plot
        window : int
            Number of candles to display
        """
        if (ticker not in self.breaker_setups or 
            timeframe not in self.breaker_setups[ticker] or
            not self.breaker_setups[ticker][timeframe] or 
            setup_idx >= len(self.breaker_setups[ticker][timeframe])):
            logger.warning(f"No setup at index {setup_idx} for {ticker} on {timeframe}")
            return
        
        # Get the setup and data
        setup = self.breaker_setups[ticker][timeframe][setup_idx]
        df = self.data[ticker][timeframe]
        
        # Get indices for key points
        sweep_idx = setup['sweep_idx']
        breaker_idx = setup['breaker_idx']
        fvg_bpr_idx = setup['fvg_bpr_idx']
        
        # Define the window to display
        start_idx = max(0, sweep_idx - window//4)
        end_idx = min(len(df), fvg_bpr_idx + window//2)
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Plot candlesticks
        for i in range(start_idx, end_idx):
            # Determine candle color
            if df.iloc[i]['close'] >= df.iloc[i]['open']:
                color = 'green'
                bottom = df.iloc[i]['open']
                height = df.iloc[i]['close'] - df.iloc[i]['open']
            else:
                color = 'red'
                bottom = df.iloc[i]['close']
                height = df.iloc[i]['open'] - df.iloc[i]['close']
            
            # Plot the body
            rect = patches.Rectangle(
                (i, bottom), 0.8, height,
                linewidth=1, edgecolor=color, facecolor=color, alpha=0.7
            )
            ax.add_patch(rect)
            
            # Plot the wick
            ax.plot(
                [i + 0.4, i + 0.4], 
                [df.iloc[i]['low'], df.iloc[i]['high']],
                color='black', linewidth=1
            )
        
        # Highlight the liquidity sweep
        if setup['type'] == 'bullish':
            sweep_level = setup['sweep_level']
            ax.axhline(y=sweep_level, color='red', linestyle='--', linewidth=1.5)
            ax.plot(
                sweep_idx + 0.4, sweep_level,
                marker='o', markersize=10, color='red',
                label='Liquidity Sweep (Sell-Side)'
            )
        else:
            sweep_level = setup['sweep_level']
            ax.axhline(y=sweep_level, color='blue', linestyle='--', linewidth=1.5)
            ax.plot(
                sweep_idx + 0.4, sweep_level,
                marker='o', markersize=10, color='blue',
                label='Liquidity Sweep (Buy-Side)'
            )
        
        # Highlight the breaker block
        breaker_high = setup['breaker_high']
        breaker_low = setup['breaker_low']
        rect = patches.Rectangle(
            (breaker_idx - 0.4, breaker_low), 0.8, breaker_high - breaker_low,
            linewidth=2, edgecolor='gold', facecolor='gold', alpha=0.5,
            label='Breaker Block'
        )
        ax.add_patch(rect)
        
        # Highlight the FVG/BPR
        if setup['imbalance_type'] == 'FVG':
            imb_low = setup['imbalance_low']
            imb_high = setup['imbalance_high']
            rect = patches.Rectangle(
                (fvg_bpr_idx - 0.5, imb_low), 1, imb_high - imb_low,
                linewidth=1, edgecolor='purple', facecolor='purple', alpha=0.3,
                label=f"{setup['imbalance_type']}"
            )
            ax.add_patch(rect)
        else:  # BPR
            imb_level = setup['imbalance_level']
            ax.axhline(y=imb_level, color='purple', linestyle='-', linewidth=2,
                      label=f"{setup['imbalance_type']}")
        
        # Add entry, stop, and target levels if this is an active signal
        for signal in self.active_signals[ticker][timeframe]:
            if (signal['sweep_idx'] == sweep_idx and 
                signal['breaker_idx'] == breaker_idx and
                signal['fvg_bpr_idx'] == fvg_bpr_idx):
                
                ax.axhline(y=signal['entry_price'], color='green', linestyle='-', linewidth=2, label='Entry')
                ax.axhline(y=signal['stop_price'], color='red', linestyle='--', linewidth=2, label='Stop')
                ax.axhline(y=signal['target_price'], color='cyan', linestyle='-.', linewidth=2, label='Target')
                break
        
        # Set the axis limits and labels
        ax.set_xlim(start_idx - 1, end_idx + 1)
        min_price = df.iloc[start_idx:end_idx]['low'].min() * 0.998
        max_price = df.iloc[start_idx:end_idx]['high'].max() * 1.002
        ax.set_ylim(min_price, max_price)
        
        # Set the title and labels
        ax.set_title(f"{ticker} {setup['type'].capitalize()} Breaker Block Setup on {timeframe} Timeframe", fontsize=16)
        ax.set_xlabel('Candle Index', fontsize=12)
        ax.set_ylabel('Price', fontsize=12)
        
        # Format x-axis with dates
        if end_idx - start_idx < 50:  # Only show dates if we're not showing too many candles
            date_indices = range(start_idx, end_idx, max(1, (end_idx - start_idx) // 10))
            date_labels = [df.index[i].strftime('%Y-%m-%d\n%H:%M') for i in date_indices]
            plt.xticks(date_indices, date_labels, rotation=45)
        
        # Add a legend
        ax.legend(loc='best')
        
        # Show the plot
        plt.tight_layout()
        plt.show()
        
        # Print setup details
        print(f"\n{setup['type'].capitalize()} Breaker Block Setup Details:")
        print(f"Ticker: {ticker}")
        print(f"Timeframe: {timeframe}")
        print(f"Setup Time: {setup['fvg_bpr_time']}")
        print(f"Liquidity Sweep Level: {setup['sweep_level']:.4f}")
        print(f"Breaker Block: {setup['breaker_low']:.4f} - {setup['breaker_high']:.4f}")
        
        if setup['imbalance_type'] == 'FVG':
            print(f"FVG: {setup['imbalance_low']:.4f} - {setup['imbalance_high']:.4f}")
        else:
            print(f"BPR Level: {setup['imbalance_level']:.4f}")
        
        # Print signal details if active
        for signal in self.active_signals[ticker][timeframe]:
            if (signal['sweep_idx'] == sweep_idx and 
                signal['breaker_idx'] == breaker_idx and
                signal['fvg_bpr_idx'] == fvg_bpr_idx):
                
                print("\nActive Signal:")
                print(f"Entry Price: {signal['entry_price']:.4f}")
                print(f"Stop Loss: {signal['stop_price']:.4f}")
                print(f"Take Profit: {signal['target_price']:.4f}")
                
                risk = abs(signal['entry_price'] - signal['stop_price'])
                reward = abs(signal['target_price'] - signal['entry_price'])
                rr_ratio = reward / risk
                
                print(f"Risk: {risk:.4f}")
                print(f"Reward: {reward:.4f}")
                print(f"Risk-Reward Ratio: {rr_ratio:.2f}")
                break

    def format_setup_for_notification(self, ticker, timeframe, signal):
        """
        Format setup information for notification
        
        Parameters:
        -----------
        ticker : str
            Ticker symbol
        timeframe : str
            Timeframe of the setup
        signal : dict
            Signal details
        
        Returns:
        --------
        str
            Formatted notification message
        """
        setup_time = signal['fvg_bpr_time'].strftime('%Y-%m-%d %H:%M')
        signal_time = signal['signal_time'].strftime('%Y-%m-%d %H:%M')
        
        message = f"🚨 BREAKER BLOCK SETUP: {ticker} ({timeframe})\n"
        message += f"Type: {signal['type'].upper()}\n"
        message += f"Setup Time: {setup_time}\n"
        message += f"Signal Time: {signal_time}\n"
        message += f"Entry: {signal['entry_price']:.4f}\n"
        message += f"Stop: {signal['stop_price']:.4f}\n"
        message += f"Target: {signal['target_price']:.4f}\n"
        message += f"Risk/Reward: 1:{signal['risk_reward_ratio']:.2f}\n"
        
        if signal['imbalance_type'] == 'FVG':
            message += f"Imbalance: FVG ({signal['imbalance_low']:.4f} - {signal['imbalance_high']:.4f})\n"
        else:
            message += f"Imbalance: BPR ({signal['imbalance_level']:.4f})\n"
        
        return message
    
    def export_to_csv(self, filename="breaker_block_signals.csv"):
        """
        Export all active signals to CSV
        
        Parameters:
        -----------
        filename : str
            Output CSV filename
        """
        all_signals = self.get_all_active_signals()
        
        if not all_signals:
            logger.warning("No active signals to export")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(all_signals)
        
        # Select columns to export
        cols = [
            'ticker', 'timeframe', 'type', 'signal_time', 'entry_price', 
            'stop_price', 'target_price', 'risk_amount', 'reward_amount', 
            'risk_reward_ratio', 'imbalance_type'
        ]
        
        # Export to CSV
        df[cols].to_csv(filename, index=False)
        logger.info(f"Exported {len(all_signals)} signals to {filename}")
        
        return df[cols]

# Example of integration with IBKR app
def ibkr_integration_example():
    """
    Example of how to integrate with an IBKR app
    
    This is a template to show how the detector would be used
    with a live data feed from IBKR
    """
    # Initialize the detector
    detector = BreakerBlockSetupDetector(timeframes=['15m', '30m', '1h', '4h'])
    
    # Example function to handle new data from IBKR
    def process_new_data(ticker, timeframe, df):
        # Process the data through the detector
        _, setups, signals = detector.process_data(ticker, timeframe, df)
        
        # If new signals were found, notify
        if signals:
            for signal in signals:
                # Format notification
                message = detector.format_setup_for_notification(ticker, timeframe, signal)
                
                # Send notification (this would be implemented by your app)
                print(message)
                
                # Optionally, plot the setup
                detector.plot_setup(ticker, timeframe, 0)
    
    # Example of processing historical data
    def load_historical_data(ticker, timeframe, lookback_days=30):
        # This would be replaced with your IBKR data loading function
        # Here we're just creating random data for illustration
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Number of candles based on timeframe
        if timeframe == '15m':
            periods = lookback_days * 24 * 4  # 15-minute candles
        elif timeframe == '30m':
            periods = lookback_days * 24 * 2  # 30-minute candles
        elif timeframe == '1h':
            periods = lookback_days * 24      # 1-hour candles
        else:  # '4h'
            periods = lookback_days * 6       # 4-hour candles
            
        # Generate dates
        dates = pd.date_range(start=start_date, end=end_date, periods=periods)
        
        # Generate price data
        prices = np.random.normal(0, 1, periods).cumsum() + 100
        
        # Create OHLC data
        df = pd.DataFrame({
            'open': prices + np.random.normal(0, 0.1, periods),
            'high': prices + np.random.normal(0.5, 0.1, periods),
            'low': prices + np.random.normal(-0.5, 0.1, periods),
            'close': prices + np.random.normal(0, 0.1, periods),
            'volume': np.random.randint(1000, 10000, periods)
        }, index=dates)
        
        return df
    
    # Example of initializing with historical data
    def initialize_ticker_data(ticker):
        for timeframe in detector.timeframes:
            # Load historical data
            df = load_historical_data(ticker, timeframe)
            
            # Process initial data
            process_new_data(ticker, timeframe, df)
    
    # Example of handling real-time updates
    def on_new_candle(ticker, timeframe, new_candle):
        # Get the current data for this ticker and timeframe
        current_data = detector.data[ticker][timeframe].copy()
        
        # Append the new candle
        current_data.loc[new_candle.name] = new_candle
        
        # Process the updated data
        process_new_data(ticker, timeframe, current_data)
    
    # Initialize some example tickers
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
    for ticker in tickers:
        initialize_ticker_data(ticker)
    
    # Export current signals to CSV
    detector.export_to_csv()
    
    # This would be replaced with your actual event loop
    print("Setup complete, now monitoring for new signals...")

class BreakerBlockAgent(BaseAgent):
    """Agent responsible for scanning for breaker block setups and retests.
    
    This agent identifies breaker blocks (former support/resistance areas) and
    detects when price returns to test these levels. It integrates advanced
    ICT-based methodologies to identify liquidity sweeps, fair value gaps (FVG),
    and breaker block setups.
    """
    
    def __init__(self, agent_id: str = "breaker_block_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the Breaker Block Agent."""
        super().__init__(agent_id, config or {})
        config = config or {}
        
        # Configuration parameters
        self.min_touches = config.get("min_touches", 2)
        self.retest_threshold = config.get("retest_threshold", 0.005)
        self.window_size = config.get("window_size", 5)
        self.fvg_threshold = config.get("fvg_threshold", 0.0015)
        self.setup_ttl_days = config.get("setup_ttl_days", 30)
        
        # Storage containers
        self.breaker_blocks = {}  # Dictionary to store breaker blocks by ticker and timeframe
        self.support_resistance = {}  # Dictionary to store support/resistance levels
        self.breaker_setups = {}  # Dictionary to store setup details
        self.active_signals = {}  # Dictionary to track active trade signals
        
        # Setup detector logic 
        self.detector = BreakerBlockSetupDetector()
        
        logger.info(f"BreakerBlockAgent initialized with config: {config}")
        
    async def validate(self, data: Any) -> bool:
        """
        Validate input data.
        
        The data should have:
        - ticker: The ticker symbol
        - timeframe: The timeframe of the data
        - ohlc_data: OHLC data as a pandas DataFrame
        """
        if not isinstance(data, dict):
            logger.error(f"Invalid data type: {type(data)}")
            return False
            
        required_keys = ['ticker', 'timeframe', 'ohlc_data']
        for key in required_keys:
            if key not in data:
                logger.error(f"Missing required key: {key}")
                return False
                
        # Validate OHLC data
        ohlc_data = data.get('ohlc_data')
        if not isinstance(ohlc_data, pd.DataFrame):
            logger.error(f"ohlc_data must be a pandas DataFrame, got {type(ohlc_data)}")
            return False
            
        required_columns = ['open', 'high', 'low', 'close']
        for col in required_columns:
            if col not in ohlc_data.columns:
                logger.error(f"Missing required column in ohlc_data: {col}")
                return False
                
        logger.debug(f"Data validation successful for {data.get('ticker')} on {data.get('timeframe')}")
        return True
        
    async def process(self, data: Dict[str, Any]) -> BreakerBlockScan:
        """
        Process price data to identify breaker blocks and retests.
        
        This method analyzes price data to identify support/resistance levels,
        detect when these levels are broken (creating breaker blocks),
        and identify when price returns to test these breaker blocks.
        
        Args:
            data: Dictionary containing ticker, timeframe, and OHLC data
            
        Returns:
            BreakerBlockScan: Results of the scan
        """
        ticker = data.get('ticker')
        timeframe = data.get('timeframe')
        ohlc_data = data.get('ohlc_data')
        
        logger.info(f"Processing {ticker} on {timeframe} timeframe with {len(ohlc_data)} candles")
        
        # Initialize ticker if not already done
        if ticker not in self.detector.breaker_setups:
            self.detector.initialize_ticker(ticker)
            
        # Process data with the detector
        _, setups, active_signals = self.detector.process_data(ticker, timeframe, ohlc_data)
        
        # Convert active signals to BreakerBlock objects
        active_breaker_blocks = []
        for signal in active_signals:
            try:
                # Create BreakerBlock from signal
                block = BreakerBlock(
                    ticker=ticker,
                    timeframe=timeframe,
                    high=signal.get('high', 0),
                    low=signal.get('low', 0),
                    direction=signal.get('direction', 'unknown'),
                    strength=signal.get('strength', 0.5),
                    created_at=signal.get('created_at', datetime.now()),
                    entry_zone=signal.get('entry_zone'),
                    fvg_high=signal.get('fvg_high'),
                    fvg_low=signal.get('fvg_low'),
                    sweep_level=signal.get('sweep_level'),
                    imbalance_type=signal.get('imbalance_type'),
                    notes=signal.get('notes', '')
                )
                active_breaker_blocks.append(block)
            except Exception as e:
                logger.error(f"Error converting signal to BreakerBlock: {str(e)}")
                
        # Update stored blocks for this ticker/timeframe
        key = f"{ticker}_{timeframe}"
        if key not in self.breaker_blocks:
            self.breaker_blocks[key] = []
        
        # Merge with existing blocks
        self._update_breaker_blocks(ticker, timeframe, active_breaker_blocks)
        
        # Generate analysis
        analysis = self._generate_analysis(ticker, timeframe, active_breaker_blocks)
        
        # Create scan results
        current_price = float(ohlc_data.iloc[-1]['close']) if len(ohlc_data) > 0 else 0.0
        scan_result = BreakerBlockScan(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            timeframe=timeframe,
            price=current_price,
            breaker_blocks=self._get_breaker_blocks(ticker, timeframe),
            active_retests=active_breaker_blocks,
            support_resistance_levels=[],  # Not using traditional S/R in the new approach
            analysis=analysis
        )
        
        logger.info(f"Scan complete for {ticker} on {timeframe}: {len(active_breaker_blocks)} active setups")
        return scan_result

    def _update_breaker_blocks(self, ticker: str, timeframe: str, new_blocks: List[BreakerBlock]) -> None:
        """
        Update stored breaker blocks with new blocks.
        
        Args:
            ticker: Ticker symbol
            timeframe: Timeframe of the data
            new_blocks: List of new breaker blocks to add/update
        """
        key = f"{ticker}_{timeframe}"
        if key not in self.breaker_blocks:
            self.breaker_blocks[key] = []
            
        # Add new blocks
        for new_block in new_blocks:
            # Check if block already exists
            existing = False
            for i, block in enumerate(self.breaker_blocks[key]):
                # If similar price levels, update instead of adding
                if (abs(block.high - new_block.high) / block.high < 0.01 and
                    abs(block.low - new_block.low) / block.low < 0.01 and
                    block.direction == new_block.direction):
                    # Update existing block
                    self.breaker_blocks[key][i] = new_block
                    existing = True
                    logger.debug(f"Updated existing breaker block at {new_block.high}-{new_block.low}")
                    break
                    
            if not existing:
                self.breaker_blocks[key].append(new_block)
                logger.debug(f"Added new breaker block at {new_block.high}-{new_block.low}")
                
        # Remove old blocks (more than setup_ttl_days old)
        cutoff_date = datetime.now() - timedelta(days=self.setup_ttl_days)
        self.breaker_blocks[key] = [b for b in self.breaker_blocks[key] 
                                  if b.created_at > cutoff_date]
                                  
        logger.info(f"Updated breaker blocks for {ticker}_{timeframe}: {len(self.breaker_blocks[key])} active")
        
    def _get_breaker_blocks(self, ticker: str, timeframe: str) -> List[BreakerBlock]:
        """
        Get stored breaker blocks for a ticker and timeframe.
        
        Args:
            ticker: Ticker symbol
            timeframe: Timeframe of the data
            
        Returns:
            List of breaker blocks
        """
        key = f"{ticker}_{timeframe}"
        return self.breaker_blocks.get(key, [])
        
    def _generate_analysis(self, ticker: str, timeframe: str, active_retests: List[BreakerBlock]) -> Dict[str, Any]:
        """
        Generate analysis based on breaker blocks and retests.
        
        Args:
            ticker: Ticker symbol
            timeframe: Timeframe of the data
            active_retests: List of active breaker block retests
            
        Returns:
            Analysis dictionary
        """
        analysis = {
            "ticker": ticker,
            "timeframe": timeframe,
            "time": datetime.now().isoformat(),
            "total_retests": len(active_retests),
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
        
        logger.debug(f"Generated analysis for {ticker} on {timeframe}: {analysis['directional_bias']} bias")
        return analysis
        
    def add_confluence(self, ticker: str, timeframe: str, price_level: float, direction: str) -> Tuple[bool, str]:
        """
        Add confluence to a breaker block.
        
        This method is called by other agents to add confluence to a breaker block
        when they detect a setup at a similar price level.
        
        Args:
            ticker: Ticker symbol
            timeframe: Timeframe of the data
            price_level: Price level of the confluence
            direction: Direction of the confluence
            
        Returns:
            Tuple[bool, str]: Success flag and message
        """
        key = f"{ticker}_{timeframe}"
        
        if key not in self.breaker_blocks:
            logger.warning(f"No breaker blocks found for {ticker} on {timeframe} timeframe")
            return False, f"No breaker blocks found for {ticker} on {timeframe} timeframe"
        
        # Find breaker blocks near the price level
        for i, block in enumerate(self.breaker_blocks[key]):
            # Check if price is within or near the breaker block
            if (block.low * 0.99 <= price_level <= block.high * 1.01 and
                block.direction == direction):
                # Add confluence
                self.breaker_blocks[key][i].confluence_count += 1
                logger.info(f"Added confluence to {direction} breaker block at {price_level:.2f}")
                return True, f"Added confluence to {direction} breaker block at {price_level:.2f}"
        
        logger.debug(f"No matching {direction} breaker blocks found near {price_level:.2f}")
        return False, f"No matching {direction} breaker blocks found near {price_level:.2f}"

# This allows the module to be imported or run as a script
if __name__ == "__main__":
    # Example usage
    ibkr_integration_example()