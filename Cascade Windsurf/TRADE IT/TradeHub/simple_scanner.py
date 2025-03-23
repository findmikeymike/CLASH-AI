#!/usr/bin/env python
"""
Simple Scanner - A simplified version of the setup scanner that doesn't rely on Prefect.
This scanner fetches market data and identifies basic price patterns.
"""
import os
import sys
import argparse
from datetime import datetime
import pandas as pd
import numpy as np
import yfinance as yf
from loguru import logger

class SimpleScanner:
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
        logger.info(f"Initialized SimpleScanner with lookback={lookback_periods}, "
                  f"min_volume={min_volume_threshold}, price_rejection={price_rejection_threshold}, "
                  f"fvg_threshold={fvg_threshold}")
    
    def fetch_data(self, symbol: str, timeframe: str = "1d", period: str = "1y") -> pd.DataFrame:
        """Fetch market data for the given symbol."""
        logger.info(f"Fetching data for {symbol} on {timeframe} timeframe")
        try:
            data = yf.download(symbol, period=period, interval=timeframe, progress=False)
            logger.info(f"Fetched {len(data)} data points for {symbol}")
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate basic technical indicators."""
        # Calculate SMA
        data['sma_20'] = data['Close'].rolling(window=20).mean()
        data['sma_50'] = data['Close'].rolling(window=50).mean()
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD
        data['ema_12'] = data['Close'].ewm(span=12, adjust=False).mean()
        data['ema_26'] = data['Close'].ewm(span=26, adjust=False).mean()
        data['macd'] = data['ema_12'] - data['ema_26']
        data['macd_signal'] = data['macd'].ewm(span=9, adjust=False).mean()
        
        # Calculate Bollinger Bands
        data['bb_middle'] = data['Close'].rolling(window=20).mean()
        data['bb_std'] = data['Close'].rolling(window=20).std()
        data['bb_upper'] = data['bb_middle'] + 2 * data['bb_std']
        data['bb_lower'] = data['bb_middle'] - 2 * data['bb_std']
        
        # Add candle classification
        data['body_size'] = abs(data['Close'] - data['Open'])
        data['wick_upper'] = data['High'] - np.maximum(data['Open'], data['Close'])
        data['wick_lower'] = np.minimum(data['Open'], data['Close']) - data['Low']
        data['is_bullish'] = data['Close'] > data['Open']
        
        return data
    
    def find_support_resistance(self, data: pd.DataFrame) -> list:
        """Find support and resistance levels."""
        levels = []
        
        # Drop rows with NaN values to avoid errors
        df = data.dropna().copy()
        
        # Need at least 30 data points for meaningful analysis
        if len(df) < 30:
            logger.warning("Not enough data points for support/resistance analysis")
            return levels
        
        # Find local minima and maxima
        for i in range(5, len(df) - 5):
            # Check if we have a local minimum
            if all(df['Low'].iloc[i] <= df['Low'].iloc[i-j] for j in range(1, 4)) and \
               all(df['Low'].iloc[i] <= df['Low'].iloc[i+j] for j in range(1, 4)):
                levels.append({
                    'type': 'support',
                    'price': df['Low'].iloc[i],
                    'date': df.index[i],
                    'strength': sum(1 for j in range(-10, 10) if i+j >= 0 and i+j < len(df) and 
                                  abs(df['Low'].iloc[i+j] - df['Low'].iloc[i]) < df['bb_std'].iloc[i] * 0.5)
                })
            
            # Check if we have a local maximum
            if all(df['High'].iloc[i] >= df['High'].iloc[i-j] for j in range(1, 4)) and \
               all(df['High'].iloc[i] >= df['High'].iloc[i+j] for j in range(1, 4)):
                levels.append({
                    'type': 'resistance',
                    'price': df['High'].iloc[i],
                    'date': df.index[i],
                    'strength': sum(1 for j in range(-10, 10) if i+j >= 0 and i+j < len(df) and 
                                  abs(df['High'].iloc[i+j] - df['High'].iloc[i]) < df['bb_std'].iloc[i] * 0.5)
                })
        
        # Sort levels by strength
        levels.sort(key=lambda x: x['strength'], reverse=True)
        
        # Take top 10 levels
        levels = levels[:10]
        
        logger.info(f"Found {len(levels)} significant support/resistance levels")
        return levels
    
    def find_chart_patterns(self, data: pd.DataFrame) -> list:
        """Find chart patterns like double tops, head and shoulders, etc."""
        patterns = []
        
        # Drop rows with NaN values to avoid errors
        df = data.dropna().copy()
        
        # Need at least 40 data points for meaningful pattern analysis
        if len(df) < 40:
            logger.warning("Not enough data points for pattern analysis")
            return patterns
        
        # Check for double top pattern
        for i in range(20, len(df) - 10):
            # Find a peak
            if all(df['High'].iloc[i] > df['High'].iloc[i-j] for j in range(1, 5)) and \
               all(df['High'].iloc[i] > df['High'].iloc[i+j] for j in range(1, 5)):
                # Look for another peak of similar height within next 10-20 bars
                for j in range(i+5, min(i+20, len(df)-5)):
                    if all(df['High'].iloc[j] > df['High'].iloc[j-k] for k in range(1, 3) if k != j-i) and \
                       all(df['High'].iloc[j] > df['High'].iloc[j+k] for k in range(1, 3)) and \
                       abs(df['High'].iloc[j] - df['High'].iloc[i]) < df['bb_std'].iloc[i]:
                        # Find the trough between the peaks
                        trough_idx = df['Low'].iloc[i:j].idxmin()
                        trough_value = df['Low'].loc[trough_idx]
                        
                        # Store the double top pattern
                        patterns.append({
                            'type': 'double_top',
                            'first_peak': df.index[i],
                            'second_peak': df.index[j],
                            'trough': trough_idx,
                            'price_level': df['High'].iloc[i],
                            'target': trough_value,
                            'strength': 5 - abs(df['High'].iloc[j] - df['High'].iloc[i]) / df['bb_std'].iloc[i] * 5
                        })
        
        # Check for other patterns here...
        
        # Sort patterns by strength
        patterns.sort(key=lambda x: x['strength'], reverse=True)
        
        logger.info(f"Found {len(patterns)} chart patterns")
        return patterns
    
    def analyze_trend(self, data: pd.DataFrame) -> dict:
        """Analyze the trend of the symbol."""
        df = data.dropna().copy()
        
        # Need at least 50 data points for meaningful trend analysis
        if len(df) < 50:
            logger.warning("Not enough data points for trend analysis")
            # Return default values instead of minimal dict
            return {
                'trend': 'unknown',
                'strength': 0.0,
                'price': float(df['Close'].iloc[-1]) if not df.empty else 0.0,
                'sma20': float(df['sma_20'].iloc[-1]) if not df.empty and 'sma_20' in df else 0.0,
                'sma50': float(df['sma_50'].iloc[-1]) if not df.empty and 'sma_50' in df else 0.0,
                'rsi': float(df['rsi'].iloc[-1]) if not df.empty and 'rsi' in df else 50.0,
                'macd': float(df['macd'].iloc[-1]) if not df.empty and 'macd' in df else 0.0,
                'macd_signal': float(df['macd_signal'].iloc[-1]) if not df.empty and 'macd_signal' in df else 0.0,
                'overbought': False,
                'oversold': False,
                'macd_crossover': False
            }
        
        # Determine trend based on SMA relationships
        price = float(df['Close'].iloc[-1])
        sma20 = float(df['sma_20'].iloc[-1])
        sma50 = float(df['sma_50'].iloc[-1])
        
        # Check trend direction and calculate strength
        if price > sma20 and sma20 > sma50:
            trend = 'bullish'
            strength = min(1.0, (price - sma50) / (sma50 * 0.1))
        elif price < sma20 and sma20 < sma50:
            trend = 'bearish'
            strength = min(1.0, (sma50 - price) / (sma50 * 0.1))
        elif price > sma20 and sma20 < sma50:
            trend = 'bullish_reversal'
            strength = min(1.0, (price - sma20) / (sma20 * 0.05))
        elif price < sma20 and sma20 > sma50:
            trend = 'bearish_reversal'
            strength = min(1.0, (sma20 - price) / (sma20 * 0.05))
        else:
            trend = 'sideways'
            strength = 0.5
        
        rsi = float(df['rsi'].iloc[-1])
        macd = float(df['macd'].iloc[-1])
        macd_signal = float(df['macd_signal'].iloc[-1])
        
        # Check MACD crossover using individual values
        macd_crossover = False
        if len(df) > 2:
            prev_macd = float(df['macd'].iloc[-2])
            prev_macd_signal = float(df['macd_signal'].iloc[-2])
            macd_crossover = (macd > macd_signal and prev_macd <= prev_macd_signal) or \
                             (macd < macd_signal and prev_macd >= prev_macd_signal)
        
        result = {
            'trend': trend,
            'strength': float(strength),
            'price': price,
            'sma20': sma20,
            'sma50': sma50,
            'rsi': rsi,
            'macd': macd,
            'macd_signal': macd_signal,
            'overbought': rsi > 70,
            'oversold': rsi < 30,
            'macd_crossover': macd_crossover
        }
        
        logger.info(f"Trend analysis: {trend} (strength: {strength:.2f})")
        return result
    
    def scan(self, symbol: str, timeframe: str = "1d", period: str = "1y") -> dict:
        """
        Scan the given symbol for trading setups.
        
        Returns a dictionary with the scan results.
        """
        logger.info(f"Scanning {symbol} on {timeframe} timeframe")
        
        # Fetch data
        data = self.fetch_data(symbol, timeframe, period)
        if data.empty:
            logger.error(f"No data available for {symbol}")
            return {'symbol': symbol, 'error': 'No data available'}
        
        try:
            # Calculate indicators
            data = self._calculate_indicators(data)
            
            # Find support and resistance levels
            support_resistance = self.find_support_resistance(data)
            
            # Find chart patterns
            patterns = self.find_chart_patterns(data)
            
            # Analyze trend
            trend_analysis = self.analyze_trend(data)
            
            # Current market price
            current_price = data['Close'].iloc[-1]
            
            # Identify potential trading setups
            setups = []
            
            # Check for trend-based setups
            if trend_analysis.get('trend') == 'bullish' and trend_analysis.get('strength', 0) > 0.7:
                # Look for pullbacks to support
                for level in support_resistance:
                    if level['type'] == 'support' and \
                       abs(current_price - level['price']) / current_price < 0.05:
                        setups.append({
                            'type': 'bullish_pullback',
                            'entry': float(current_price),
                            'stop_loss': float(level['price'] * 0.98),  # 2% below support
                            'target': float(current_price * 1.1),  # 10% profit target
                            'confidence': float(trend_analysis['strength'] * level['strength'] / 10),
                            'description': f"Bullish pullback to support at {level['price']:.2f}"
                        })
            
            elif trend_analysis.get('trend') == 'bearish' and trend_analysis.get('strength', 0) > 0.7:
                # Look for rallies to resistance
                for level in support_resistance:
                    if level['type'] == 'resistance' and \
                       abs(current_price - level['price']) / current_price < 0.05:
                        setups.append({
                            'type': 'bearish_rally',
                            'entry': float(current_price),
                            'stop_loss': float(level['price'] * 1.02),  # 2% above resistance
                            'target': float(current_price * 0.9),  # 10% profit target
                            'confidence': float(trend_analysis['strength'] * level['strength'] / 10),
                            'description': f"Bearish rally to resistance at {level['price']:.2f}"
                        })
            
            # Check for pattern-based setups
            for pattern in patterns:
                if pattern['type'] == 'double_top' and current_price < pattern['price_level']:
                    setups.append({
                        'type': 'double_top_breakdown',
                        'entry': float(current_price),
                        'stop_loss': float(pattern['price_level'] * 1.02),
                        'target': float(pattern['target']),
                        'confidence': float(pattern['strength'] / 5),
                        'description': f"Double top breakdown at {pattern['price_level']:.2f}"
                    })
            
            # Safely check conditions that might not be present in limited data scenarios
            is_oversold = trend_analysis.get('oversold', False)
            is_overbought = trend_analysis.get('overbought', False)
            trend = trend_analysis.get('trend', 'unknown')
            macd_crossover = trend_analysis.get('macd_crossover', False)
            macd = trend_analysis.get('macd', 0)
            macd_signal = trend_analysis.get('macd_signal', 0)
            
            # Add RSI-based setups
            if is_oversold and trend != 'bearish':
                setups.append({
                    'type': 'oversold_bounce',
                    'entry': float(current_price),
                    'stop_loss': float(current_price * 0.97),
                    'target': float(current_price * 1.05),
                    'confidence': 0.6,
                    'description': f"Oversold bounce with RSI at {trend_analysis.get('rsi', 0):.1f}"
                })
            
            if is_overbought and trend != 'bullish':
                setups.append({
                    'type': 'overbought_pullback',
                    'entry': float(current_price),
                    'stop_loss': float(current_price * 1.03),
                    'target': float(current_price * 0.95),
                    'confidence': 0.6,
                    'description': f"Overbought pullback with RSI at {trend_analysis.get('rsi', 0):.1f}"
                })
            
            # Add MACD crossover setups
            if macd_crossover:
                if macd > macd_signal:
                    setups.append({
                        'type': 'macd_bullish_crossover',
                        'entry': float(current_price),
                        'stop_loss': float(current_price * 0.97),
                        'target': float(current_price * 1.05),
                        'confidence': 0.7,
                        'description': "MACD bullish crossover"
                    })
                else:
                    setups.append({
                        'type': 'macd_bearish_crossover',
                        'entry': float(current_price),
                        'stop_loss': float(current_price * 1.03),
                        'target': float(current_price * 0.95),
                        'confidence': 0.7,
                        'description': "MACD bearish crossover"
                    })
            
            # Sort setups by confidence
            setups.sort(key=lambda x: x['confidence'], reverse=True)
            
            result = {
                'symbol': symbol,
                'timeframe': timeframe,
                'current_price': float(current_price),
                'timestamp': datetime.now().isoformat(),
                'trend_analysis': trend_analysis,
                'support_resistance': support_resistance,
                'chart_patterns': patterns,
                'setups': setups,
                'total_setups': len(setups)
            }
            
            logger.info(f"Scan completed for {symbol}. Found {len(setups)} potential setups.")
            return result
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {str(e)}")
            # Return a basic result with error information
            return {
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'setups': [],
                'total_setups': 0
            }

def main():
    """Main function to run the scanner."""
    parser = argparse.ArgumentParser(description="Run the simplified scanner")
    parser.add_argument("--symbols", type=str, nargs="+", default=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
                        help="List of symbols to scan")
    parser.add_argument("--timeframe", type=str, default="1d",
                        help="Timeframe to use (e.g., 1d, 1h, 15m)")
    parser.add_argument("--period", type=str, default="1y",
                        help="Period to fetch data for (e.g., 1d, 5d, 1mo, 1y, 2y)")
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add("logs/scanner_{time}.log", rotation="500 MB", level="DEBUG")
    
    # Initialize scanner
    scanner = SimpleScanner()
    
    # Scan each symbol
    results = []
    for symbol in args.symbols:
        try:
            result = scanner.scan(symbol, args.timeframe, args.period)
            results.append(result)
            
            # Print results
            print(f"\n===== {symbol} =====")
            
            # Check for error in result
            if 'error' in result:
                print(f"Error: {result['error']}")
                continue
                
            print(f"Current price: ${result.get('current_price', 0.0):.2f}")
            
            # Safely access trend analysis
            trend_analysis = result.get('trend_analysis', {})
            print(f"Trend: {trend_analysis.get('trend', 'unknown')} (strength: {trend_analysis.get('strength', 0.0):.2f})")
            print(f"RSI: {trend_analysis.get('rsi', 0.0):.1f}")
            
            if result.get('setups', []):
                print(f"\nFound {len(result['setups'])} potential setups:")
                for i, setup in enumerate(result['setups'], 1):
                    print(f"{i}. {setup['type']} - {setup['description']}")
                    print(f"   Entry: ${setup['entry']:.2f}, Stop: ${setup['stop_loss']:.2f}, Target: ${setup['target']:.2f}")
                    print(f"   Confidence: {setup['confidence']:.2f}")
            else:
                print("\nNo setups found.")
            
            print("=" * (len(symbol) + 12))
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {str(e)}")
    
    # Print summary
    total_setups = sum(len(result.get('setups', [])) for result in results)
    print(f"\nScan completed. Found {total_setups} potential setups across {len(args.symbols)} symbols.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 