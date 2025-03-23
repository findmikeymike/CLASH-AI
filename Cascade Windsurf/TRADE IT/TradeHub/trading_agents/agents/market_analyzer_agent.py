import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import talib
import logging
import json
from typing import Dict, List, Tuple, Any, Optional
from prefect import task, flow
from prefect.tasks import task_input_hash
from loguru import logger

from .base_agent import BaseAgent

class MarketAnalyzerAgent(BaseAgent):
    """
    Agent responsible for analyzing market context and sector rotation.
    Provides overall market sentiment, sector analysis, and tags for trade setups.
    """
    
    def __init__(self, name: str = "market_analyzer", config: Optional[Dict[str, Any]] = None):
        """Initialize the MarketAnalyzerAgent with configuration"""
        super().__init__(name, config)
        config = config or {}
        
        # Configure agent-specific parameters
        self.market_tickers = config.get('market_tickers', ['^GSPC', 'QQQ', 'IWM', 'SPY'])
        self.sector_tickers = config.get('sector_tickers', ['XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLB', 'XLRE'])
        self.options_tickers = config.get('options_tickers', ['SPY', 'QQQ'])
        self.sentiment_keywords = config.get('sentiment_keywords', ['market', 'stocks', 'economy', 'fed', 'inflation'])
        self.cache_ttl = config.get('cache_ttl', 60)  # minutes
        
        # Initialize cache for analysis results
        self._cache = {}
        self._cache_timestamp = {}
        
        logger.info(f"Initialized {name} with {len(self.market_tickers)} market tickers and {len(self.sector_tickers)} sector tickers")
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process market data to provide context for trade setups
        
        Args:
            data: Dictionary containing ticker data and potential setups
            
        Returns:
            Dictionary with market analysis and tagged setups
        """
        logger.info(f"Processing market analysis for {len(data.get('tickers', []))} tickers")
        
        # Check if we have a recent market analysis
        if self._is_cache_valid('market_analysis'):
            market_analysis = self._get_from_cache('market_analysis')
            logger.info("Using cached market analysis")
        else:
            # Run market analysis flow
            market_analysis = self._run_market_analysis()
            self._add_to_cache('market_analysis', market_analysis)
        
        # Check if we have recent sector analysis
        if self._is_cache_valid('sector_analysis'):
            sector_analysis = self._get_from_cache('sector_analysis')
            logger.info("Using cached sector analysis")
        else:
            # Run sector analysis
            sector_analysis = self._analyze_sectors()
            self._add_to_cache('sector_analysis', sector_analysis)
        
        # Tag setups with market context if setups exist in data
        if 'setups' in data and data['setups']:
            data['setups'] = self._tag_setups_with_market_context(
                data['setups'], 
                market_analysis, 
                sector_analysis
            )
        
        # Add market and sector analysis to the result
        data['market_analysis'] = market_analysis
        data['sector_analysis'] = sector_analysis
        
        return data
    
    def _run_market_analysis(self) -> Dict[str, Any]:
        """Run the market analysis flow"""
        logger.info("Running market analysis flow")
        
        # Data collection
        market_data = self._fetch_market_data(self.market_tickers)
        options_data = self._fetch_options_data(self.options_tickers)
        economic_data = self._fetch_economic_data()
        
        # Analysis
        trend_analysis = self._analyze_market_trend(market_data)
        options_analysis = self._analyze_options_flow(options_data)
        gex_analysis = self._calculate_gamma_exposure(options_data, market_data)
        intermarket_analysis = self._analyze_intermarket_relations(market_data, economic_data)
        
        # Market regime detection
        regime_analysis = self._detect_market_regime(market_data)
        
        # Consolidation
        market_analysis = self._consolidate_market_analysis(
            trend_analysis,
            options_analysis,
            gex_analysis,
            intermarket_analysis,
            regime_analysis
        )
        
        return market_analysis
    
    def _analyze_sectors(self) -> Dict[str, Any]:
        """Analyze sector performance and rotation"""
        logger.info(f"Analyzing {len(self.sector_tickers)} sectors")
        
        # Fetch sector data
        sector_data = self._fetch_market_data(self.sector_tickers, period="3mo")
        spx_data = self._fetch_market_data(['^GSPC'], period="3mo")['^GSPC']
        
        sector_analysis = {
            'timestamp': datetime.now().isoformat(),
            'relative_strength': {},
            'momentum': {},
            'leading_sectors': [],
            'lagging_sectors': [],
            'rotation_signals': {}
        }
        
        # Calculate relative strength vs SPX
        for sector, data in sector_data.items():
            if len(data) < 20 or len(spx_data) < 20:
                continue
                
            # Align dates
            common_dates = data.index.intersection(spx_data.index)
            if len(common_dates) < 20:
                continue
                
            sector_prices = data.loc[common_dates, 'Close']
            spx_prices = spx_data.loc[common_dates, 'Close']
            
            # Normalize to starting point
            sector_norm = sector_prices / sector_prices.iloc[0]
            spx_norm = spx_prices / spx_prices.iloc[0]
            
            # Calculate relative strength
            rs = sector_norm / spx_norm
            
            # Calculate momentum (rate of change)
            sector_momentum_1m = sector_prices.pct_change(20).iloc[-1] * 100  # ~1 month
            sector_momentum_2w = sector_prices.pct_change(10).iloc[-1] * 100  # ~2 weeks
            sector_momentum_1w = sector_prices.pct_change(5).iloc[-1] * 100   # ~1 week
            
            # Store results
            sector_analysis['relative_strength'][sector] = {
                'current': rs.iloc[-1],
                'change_1m': rs.iloc[-1] / rs.iloc[-20] - 1 if len(rs) >= 20 else None,
                'change_2w': rs.iloc[-1] / rs.iloc[-10] - 1 if len(rs) >= 10 else None,
                'trend': 'improving' if rs.iloc[-1] > rs.iloc[-5] else 'weakening'
            }
            
            sector_analysis['momentum'][sector] = {
                '1m': sector_momentum_1m,
                '2w': sector_momentum_2w,
                '1w': sector_momentum_1w
            }
        
        # Identify leading and lagging sectors
        if sector_analysis['relative_strength']:
            # Sort sectors by relative strength
            sorted_sectors = sorted(
                sector_analysis['relative_strength'].items(),
                key=lambda x: x[1]['current'],
                reverse=True
            )
            
            # Top 3 are leading, bottom 3 are lagging
            sector_analysis['leading_sectors'] = [s[0] for s in sorted_sectors[:3]]
            sector_analysis['lagging_sectors'] = [s[0] for s in sorted_sectors[-3:]]
            
            # Detect rotation signals
            for sector, data in sector_analysis['relative_strength'].items():
                # Rotation into sector: improving RS and positive momentum
                if (data['trend'] == 'improving' and 
                    sector_analysis['momentum'][sector]['1w'] > 0 and
                    sector_analysis['momentum'][sector]['2w'] > sector_analysis['momentum'][sector]['1m']):
                    sector_analysis['rotation_signals'][sector] = 'rotating_in'
                
                # Rotation out of sector: weakening RS and negative momentum
                elif (data['trend'] == 'weakening' and 
                      sector_analysis['momentum'][sector]['1w'] < 0 and
                      sector_analysis['momentum'][sector]['2w'] < sector_analysis['momentum'][sector]['1m']):
                    sector_analysis['rotation_signals'][sector] = 'rotating_out'
                
                # No clear rotation signal
                else:
                    sector_analysis['rotation_signals'][sector] = 'stable'
        
        return sector_analysis
    
    def _tag_setups_with_market_context(
        self, 
        setups: List[Dict[str, Any]], 
        market_analysis: Dict[str, Any],
        sector_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Tag trade setups with market context information
        
        Args:
            setups: List of trade setups
            market_analysis: Market analysis results
            sector_analysis: Sector analysis results
            
        Returns:
            Updated list of setups with market context tags
        """
        logger.info(f"Tagging {len(setups)} setups with market context")
        
        market_stance = market_analysis.get('stance', 'neutral')
        market_regime = market_analysis.get('regime', 'undefined')
        
        for setup in setups:
            ticker = setup.get('ticker', '')
            direction = setup.get('direction', '')
            
            # Initialize market context tags
            setup['market_context'] = {
                'market_aligned': False,
                'sector_aligned': False,
                'market_stance': market_stance,
                'market_regime': market_regime,
                'sector_status': 'unknown',
                'confidence_adjustment': 0.0,
                'risk_adjustment': 0.0,
                'tags': []
            }
            
            # Check market alignment
            if (direction == 'bullish' and market_stance == 'bullish') or \
               (direction == 'bearish' and market_stance == 'bearish'):
                setup['market_context']['market_aligned'] = True
                setup['market_context']['confidence_adjustment'] += 0.1
                setup['market_context']['tags'].append('aligned_with_market')
            elif (direction == 'bullish' and market_stance == 'bearish') or \
                 (direction == 'bearish' and market_stance == 'bullish'):
                setup['market_context']['confidence_adjustment'] -= 0.1
                setup['market_context']['tags'].append('against_market')
            else:
                setup['market_context']['tags'].append('neutral_market')
            
            # Apply regime-specific adjustments
            if market_regime == 'volatile':
                # In volatile markets, reduce position size and widen stops
                setup['market_context']['risk_adjustment'] -= 0.2  # Reduce position size by 20%
                setup['market_context']['tags'].append('volatile_market')
                
                # Suggest wider stops in volatile markets
                if 'stop_loss' in setup and 'entry_price' in setup:
                    entry = setup['entry_price']
                    stop = setup['stop_loss']
                    direction_mult = 1 if direction == 'bullish' else -1
                    
                    # If stop is too close in volatile market, flag it
                    stop_pct = abs(entry - stop) / entry * 100
                    if stop_pct < 1.5:  # Less than 1.5% stop in volatile market
                        setup['market_context']['tags'].append('stop_too_tight')
                
            elif 'trending' in market_regime:
                # In trending markets, we can be more confident in trend-following setups
                if (market_regime == 'trending_bullish' and direction == 'bullish') or \
                   (market_regime == 'trending_bearish' and direction == 'bearish'):
                    setup['market_context']['confidence_adjustment'] += 0.15
                    setup['market_context']['tags'].append('with_trend')
                else:
                    setup['market_context']['confidence_adjustment'] -= 0.1
                    setup['market_context']['tags'].append('counter_trend')
                    
            elif market_regime == 'ranging':
                # In ranging markets, mean-reversion setups work better
                # Identify if this is a breakout or mean-reversion setup
                setup_type = setup.get('setup_type', '').lower()
                
                if 'breakout' in setup_type:
                    setup['market_context']['confidence_adjustment'] -= 0.1
                    setup['market_context']['tags'].append('breakout_in_range')
                elif any(pattern in setup_type for pattern in ['support', 'resistance', 'retest']):
                    setup['market_context']['confidence_adjustment'] += 0.1
                    setup['market_context']['tags'].append('mean_reversion')
            
            elif market_regime == 'reversal':
                # In potential reversal regimes, be cautious with trend continuation
                if (market_regime == 'reversal' and 
                    ((market_stance == 'bullish' and direction == 'bearish') or 
                     (market_stance == 'bearish' and direction == 'bullish'))):
                    setup['market_context']['confidence_adjustment'] += 0.1
                    setup['market_context']['tags'].append('potential_reversal')
            
            # Check sector alignment if we have sector information
            sector = self._get_ticker_sector(ticker)
            if sector and sector in sector_analysis.get('sector_performance', {}):
                sector_status = sector_analysis['sector_performance'][sector]['status']
                setup['market_context']['sector_status'] = sector_status
                
                if (direction == 'bullish' and sector_status == 'leading') or \
                   (direction == 'bearish' and sector_status == 'lagging'):
                    setup['market_context']['sector_aligned'] = True
                    setup['market_context']['confidence_adjustment'] += 0.1
                    setup['market_context']['tags'].append('aligned_with_sector')
                elif (direction == 'bullish' and sector_status == 'lagging') or \
                     (direction == 'bearish' and sector_status == 'leading'):
                    setup['market_context']['confidence_adjustment'] -= 0.1
                    setup['market_context']['tags'].append('against_sector')
            
            # Add any market warnings
            if 'warnings' in market_analysis and market_analysis['warnings']:
                setup['market_context']['warnings'] = market_analysis['warnings']
            
            # Apply the confidence adjustment to the setup
            if 'confidence' in setup:
                setup['confidence'] = min(1.0, max(0.1, setup['confidence'] + setup['market_context']['confidence_adjustment']))
        
        return setups
    
    def _get_ticker_sector(self, ticker: str) -> Optional[str]:
        """Get the sector for a given ticker"""
        try:
            ticker_info = yf.Ticker(ticker).info
            return ticker_info.get('sector')
        except:
            return None
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache or key not in self._cache_timestamp:
            return False
            
        cache_age = datetime.now() - self._cache_timestamp[key]
        return cache_age.total_seconds() < (self.cache_ttl * 60)
    
    def _add_to_cache(self, key: str, data: Any) -> None:
        """Add data to cache with current timestamp"""
        self._cache[key] = data
        self._cache_timestamp[key] = datetime.now()
    
    def _get_from_cache(self, key: str) -> Any:
        """Get data from cache"""
        return self._cache.get(key)
    
    # Data collection methods
    def _fetch_market_data(self, tickers: List[str], period: str = "1mo") -> Dict[str, pd.DataFrame]:
        """Fetch market data for multiple tickers"""
        logger.info(f"Fetching market data for {tickers}")
        data = {}
        for ticker in tickers:
            try:
                data[ticker] = yf.download(ticker, period=period, interval="1d", progress=False)
            except Exception as e:
                logger.error(f"Error fetching data for {ticker}: {e}")
        return data
    
    def _fetch_options_data(self, tickers: List[str]) -> Dict[str, Any]:
        """Fetch options data for specified tickers"""
        logger.info(f"Fetching options data for {tickers}")
        options_data = {}
        
        for ticker in tickers:
            try:
                ticker_obj = yf.Ticker(ticker)
                options_data[ticker] = {
                    'options_chain': ticker_obj.option_chain(),
                    'expiration_dates': ticker_obj.options
                }
            except Exception as e:
                logger.error(f"Error fetching options data for {ticker}: {e}")
        
        return options_data
    
    def _fetch_economic_data(self) -> Dict[str, Any]:
        """
        Fetch relevant economic indicators
        Note: In a production environment, connect to FRED API or other sources
        """
        logger.info("Fetching economic indicators")
        
        # TODO: Replace with actual API calls to FRED or other sources
        economic_data = {
            'treasury_yields': {
                '2y': 4.5,  # Replace with actual data
                '10y': 4.2  # Replace with actual data
            },
            'inflation_data': {
                'cpi': 3.5,  # Replace with actual data
                'ppi': 3.8   # Replace with actual data
            }
        }
        
        return economic_data
    
    # Analysis methods
    def _analyze_market_trend(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """Analyze market trends using technical indicators"""
        logger.info("Analyzing market trends")
        
        trend_analysis = {}
        
        for ticker, data in market_data.items():
            if len(data) < 20:  # Need enough data for analysis
                trend_analysis[ticker] = "insufficient_data"
                continue
                
            df = data.copy()
            
            # Calculate technical indicators
            try:
                # Simple Moving Averages
                df['SMA20'] = df['Close'].rolling(window=20).mean()
                df['SMA50'] = df['Close'].rolling(window=50).mean()
                
                # RSI
                df['RSI'] = talib.RSI(df['Close'].values, timeperiod=14)
                
                # MACD
                macd, macd_signal, _ = talib.MACD(df['Close'].values, 
                                                fastperiod=12, 
                                                slowperiod=26, 
                                                signalperiod=9)
                df['MACD'] = macd
                df['MACD_Signal'] = macd_signal
                
                # Trend determination logic
                last_row = df.iloc[-1]
                
                # Simple trend determination
                if (last_row['SMA20'] > last_row['SMA50'] and 
                    last_row['Close'] > last_row['SMA20'] and 
                    last_row['RSI'] > 50 and 
                    last_row['MACD'] > last_row['MACD_Signal']):
                    trend = "bullish"
                elif (last_row['SMA20'] < last_row['SMA50'] and 
                      last_row['Close'] < last_row['SMA20'] and 
                      last_row['RSI'] < 50 and 
                      last_row['MACD'] < last_row['MACD_Signal']):
                    trend = "bearish"
                else:
                    trend = "neutral"
                    
                trend_analysis[ticker] = trend
                
            except Exception as e:
                logger.error(f"Error analyzing trend for {ticker}: {e}")
                trend_analysis[ticker] = "error"
        
        return trend_analysis
    
    def _analyze_options_flow(self, options_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Analyze options flow to determine market sentiment"""
        logger.info("Analyzing options flow")
        
        options_analysis = {}
        
        for ticker, data in options_data.items():
            try:
                # Calculate put-call ratio
                calls = data['options_chain'].calls
                puts = data['options_chain'].puts
                
                call_volume = calls['volume'].sum() if 'volume' in calls.columns else 0
                put_volume = puts['volume'].sum() if 'volume' in puts.columns else 0
                
                if call_volume > 0:
                    put_call_ratio = put_volume / call_volume
                else:
                    put_call_ratio = float('inf')
                
                # Calculate call and put open interest
                call_oi = calls['openInterest'].sum() if 'openInterest' in calls.columns else 0
                put_oi = puts['openInterest'].sum() if 'openInterest' in puts.columns else 0
                
                # Calculate implied volatility spread
                if 'impliedVolatility' in calls.columns and 'impliedVolatility' in puts.columns:
                    avg_call_iv = calls['impliedVolatility'].mean()
                    avg_put_iv = puts['impliedVolatility'].mean()
                    iv_spread = avg_put_iv - avg_call_iv
                else:
                    avg_call_iv = avg_put_iv = iv_spread = None
                
                # Determine sentiment based on options data
                if put_call_ratio > 1.5:
                    sentiment = "bearish"  # High put activity relative to calls
                elif put_call_ratio < 0.7:
                    sentiment = "bullish"  # High call activity relative to puts
                else:
                    sentiment = "neutral"
                    
                options_analysis[ticker] = {
                    'put_call_ratio': put_call_ratio,
                    'call_volume': call_volume,
                    'put_volume': put_volume,
                    'call_oi': call_oi,
                    'put_oi': put_oi,
                    'avg_call_iv': avg_call_iv,
                    'avg_put_iv': avg_put_iv,
                    'iv_spread': iv_spread,
                    'sentiment': sentiment
                }
                
            except Exception as e:
                logger.error(f"Error analyzing options data for {ticker}: {e}")
                options_analysis[ticker] = {'sentiment': 'error', 'error': str(e)}
        
        return options_analysis
    
    def _calculate_gamma_exposure(self, options_data: Dict[str, Any], market_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """Calculate approximate gamma exposure (GEX) for market impact assessment"""
        logger.info("Calculating gamma exposure")
        
        gex_analysis = {}
        
        for ticker, data in options_data.items():
            try:
                if ticker not in market_data:
                    gex_analysis[ticker] = None
                    continue
                    
                current_price = market_data[ticker]['Close'].iloc[-1]
                
                calls = data['options_chain'].calls
                puts = data['options_chain'].puts
                
                # Filter for options near current price (within 10%)
                near_calls = calls[(calls['strike'] >= current_price * 0.9) & 
                                  (calls['strike'] <= current_price * 1.1)]
                near_puts = puts[(puts['strike'] >= current_price * 0.9) & 
                                (puts['strike'] <= current_price * 1.1)]
                
                # Calculate gamma for each option and total gamma exposure
                if 'gamma' in near_calls.columns and 'openInterest' in near_calls.columns:
                    call_gamma = (near_calls['gamma'] * near_calls['openInterest'] * 100).sum()
                else:
                    call_gamma = 0
                    
                if 'gamma' in near_puts.columns and 'openInterest' in near_puts.columns:
                    # Put gamma is negative in its effect
                    put_gamma = -(near_puts['gamma'] * near_puts['openInterest'] * 100).sum()
                else:
                    put_gamma = 0
                    
                net_gamma = call_gamma + put_gamma
                
                gex_analysis[ticker] = net_gamma
                
            except Exception as e:
                logger.error(f"Error calculating GEX for {ticker}: {e}")
                gex_analysis[ticker] = None
        
        return gex_analysis
    
    def _analyze_intermarket_relations(self, market_data: Dict[str, pd.DataFrame], economic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze relationships between different market segments"""
        logger.info("Analyzing intermarket relationships")
        
        # Simplified correlation analysis between asset classes
        correlations = {}
        
        # Get key assets from different markets if available
        stock_index = market_data.get('SPY', market_data.get('^GSPC', None))
        bonds = market_data.get('TLT', None)
        gold = market_data.get('GLD', None)
        dollar = market_data.get('UUP', None)
        
        assets = {'stocks': stock_index, 'bonds': bonds, 'gold': gold, 'dollar': dollar}
        
        # Calculate correlations between available assets
        for name1, asset1 in assets.items():
            if asset1 is None or len(asset1) < 20:
                continue
                
            correlations[name1] = {}
            
            for name2, asset2 in assets.items():
                if name2 == name1 or asset2 is None or len(asset2) < 20:
                    continue
                    
                # Calculate correlation on returns
                returns1 = asset1['Close'].pct_change().dropna()
                returns2 = asset2['Close'].pct_change().dropna()
                
                # Align the data
                common_index = returns1.index.intersection(returns2.index)
                if len(common_index) > 10:
                    corr = returns1[common_index].corr(returns2[common_index])
                    correlations[name1][name2] = corr
        
        # Analyze yield curve (2y vs 10y treasury)
        try:
            two_year = economic_data['treasury_yields']['2y']
            ten_year = economic_data['treasury_yields']['10y']
            yield_spread = ten_year - two_year
            
            if yield_spread < 0:
                yield_curve = "inverted"
            elif yield_spread < 0.5:
                yield_curve = "flat"
            else:
                yield_curve = "normal"
        except:
            yield_curve = "unknown"
            yield_spread = None
        
        intermarket_analysis = {
            'correlations': correlations,
            'yield_curve': {
                'status': yield_curve,
                'spread': yield_spread
            }
        }
        
        return intermarket_analysis
    
    def _detect_market_regime(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
        """
        Detect the current market regime (trending, ranging, volatile) for each market ticker.
        
        Market regimes:
        - Trending: Strong directional movement (up or down)
        - Ranging: Price moving sideways within a channel
        - Volatile: High volatility with unpredictable movements
        - Reversal: Potential trend change
        """
        logger.info("Detecting market regimes")
        
        regime_analysis = {}
        
        for ticker, data in market_data.items():
            if len(data) < 30:  # Need enough data for regime analysis
                regime_analysis[ticker] = {
                    "regime": "unknown",
                    "confidence": 0.0,
                    "details": {}
                }
                continue
                
            df = data.copy()
            
            try:
                # Calculate indicators for regime detection
                # 1. Average True Range (ATR) for volatility
                df['ATR'] = talib.ATR(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14)
                
                # 2. Bollinger Bands for range identification
                df['BB_upper'], df['BB_middle'], df['BB_lower'] = talib.BBANDS(
                    df['Close'].values, 
                    timeperiod=20,
                    nbdevup=2,
                    nbdevdn=2,
                    matype=0
                )
                
                # 3. ADX for trend strength
                df['ADX'] = talib.ADX(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=14)
                
                # 4. Historical Volatility
                df['returns'] = df['Close'].pct_change()
                df['hist_vol'] = df['returns'].rolling(window=21).std() * np.sqrt(252)  # Annualized
                
                # Get recent values
                recent = df.iloc[-10:].copy()
                current = df.iloc[-1].copy()
                
                # Calculate BB width (normalized)
                recent['BB_width'] = (recent['BB_upper'] - recent['BB_lower']) / recent['BB_middle']
                bb_width_current = current['BB_width'] if 'BB_width' in current else (current['BB_upper'] - current['BB_lower']) / current['BB_middle']
                
                # Calculate average values
                avg_atr = recent['ATR'].mean()
                avg_adx = recent['ADX'].mean()
                avg_hist_vol = recent['hist_vol'].dropna().mean()
                
                # Normalize ATR
                normalized_atr = avg_atr / current['Close'] * 100  # As percentage of price
                
                # Regime determination logic
                regime = "unknown"
                confidence = 0.0
                details = {
                    "adx": avg_adx,
                    "normalized_atr": normalized_atr,
                    "bb_width": bb_width_current,
                    "hist_vol": avg_hist_vol
                }
                
                # Strong trend detection
                if avg_adx > 25:
                    trend_strength = min(1.0, (avg_adx - 25) / 25)  # Scale 25-50 to 0-1
                    
                    # Determine if bullish or bearish trend
                    if df['Close'].iloc[-1] > df['Close'].iloc[-20]:
                        regime = "trending_bullish"
                    else:
                        regime = "trending_bearish"
                    
                    confidence = trend_strength
                
                # Ranging market detection
                elif avg_adx < 20 and normalized_atr < 1.5:
                    range_strength = min(1.0, (20 - avg_adx) / 15)  # Scale 20-5 to 0-1
                    regime = "ranging"
                    confidence = range_strength
                
                # Volatile market detection
                elif normalized_atr > 2.0 or avg_hist_vol > 0.3:  # 30% annualized vol is high
                    vol_strength = min(1.0, normalized_atr / 4)  # Scale 2-6 to 0.5-1
                    regime = "volatile"
                    confidence = vol_strength
                
                # Potential reversal detection
                elif (avg_adx < 25 and avg_adx > 15 and 
                      abs(df['Close'].pct_change(periods=5).iloc[-1]) > 0.03):
                    regime = "reversal"
                    confidence = 0.7  # Reversals are harder to detect with high confidence
                
                # Default case - early trend or undefined
                else:
                    if avg_adx > 15:
                        regime = "early_trend"
                        confidence = avg_adx / 25  # Scale based on ADX
                    else:
                        regime = "undefined"
                        confidence = 0.5
                
                regime_analysis[ticker] = {
                    "regime": regime,
                    "confidence": confidence,
                    "details": details
                }
                
            except Exception as e:
                logger.error(f"Error detecting regime for {ticker}: {e}")
                regime_analysis[ticker] = {
                    "regime": "error",
                    "confidence": 0.0,
                    "details": {"error": str(e)}
                }
        
        return regime_analysis
    
    def _consolidate_market_analysis(
        self,
        trend_analysis: Dict[str, str],
        options_analysis: Dict[str, Dict[str, Any]],
        gex_analysis: Dict[str, float],
        intermarket_analysis: Dict[str, Any],
        regime_analysis: Dict[str, Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Consolidate all analyses into a final market assessment"""
        logger.info("Consolidating market analysis")
        
        # Count trend signals
        trend_counts = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        for ticker, trend in trend_analysis.items():
            if trend in trend_counts:
                trend_counts[trend] += 1
        
        # Options sentiment
        options_sentiment_counts = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        for ticker, analysis in options_analysis.items():
            sentiment = analysis.get('sentiment')
            if sentiment in options_sentiment_counts:
                options_sentiment_counts[sentiment] += 1
        
        # Average GEX
        valid_gex_values = [value for value in gex_analysis.values() if value is not None]
        avg_gex = sum(valid_gex_values) / len(valid_gex_values) if valid_gex_values else 0
        
        # Intermarket warning signals
        yield_curve_warning = intermarket_analysis['yield_curve']['status'] == 'inverted'
        
        # Analyze market regimes
        regime_counts = {}
        if regime_analysis:
            for ticker, analysis in regime_analysis.items():
                regime = analysis.get('regime', 'unknown')
                if regime not in regime_counts:
                    regime_counts[regime] = 0
                regime_counts[regime] += 1
        
        # Determine dominant market regime
        dominant_regime = "undefined"
        if regime_counts:
            dominant_regime = max(regime_counts.items(), key=lambda x: x[1])[0]
        
        # Compute an overall market score (-10 to +10 scale)
        market_score = 0
        
        # Contribute technical trends (max ±3)
        if trend_counts['bullish'] > trend_counts['bearish']:
            market_score += min(3, (trend_counts['bullish'] - trend_counts['bearish']))
        elif trend_counts['bearish'] > trend_counts['bullish']:
            market_score -= min(3, (trend_counts['bearish'] - trend_counts['bullish']))
        
        # Contribute options sentiment (max ±2)
        if options_sentiment_counts['bullish'] > options_sentiment_counts['bearish']:
            market_score += min(2, (options_sentiment_counts['bullish'] - options_sentiment_counts['bearish']))
        elif options_sentiment_counts['bearish'] > options_sentiment_counts['bullish']:
            market_score -= min(2, (options_sentiment_counts['bearish'] - options_sentiment_counts['bullish']))
        
        # Contribute GEX (max ±2)
        # Positive GEX tends to stabilize markets, negative GEX can amplify moves
        if avg_gex > 0:
            market_score += min(2, avg_gex / 1e6)  # Scale appropriately
        elif avg_gex < 0:
            market_score -= min(2, abs(avg_gex) / 1e6)  # Scale appropriately
            
        # Adjust score based on market regime
        if dominant_regime == "volatile":
            # In volatile regimes, reduce the absolute score (less conviction)
            market_score *= 0.7
        elif dominant_regime == "ranging":
            # In ranging markets, move score closer to neutral
            market_score *= 0.5
        elif "trending" in dominant_regime:
            # In trending markets, amplify the score slightly
            market_score *= 1.2
            
        # Cap the score to our -10 to +10 range
        market_score = max(-10, min(10, market_score))
        
        # Determine overall market stance
        if market_score > 3:
            market_stance = "bullish"
        elif market_score < -3:
            market_stance = "bearish"
        else:
            market_stance = "neutral"
            
        # Add warnings
        warnings = []
        if yield_curve_warning:
            warnings.append("Inverted yield curve detected")
        
        if dominant_regime == "volatile":
            warnings.append("High market volatility detected")
        
        if dominant_regime == "reversal":
            warnings.append("Potential market reversal detected")
            
        # Compile final analysis
        final_analysis = {
            "stance": market_stance,
            "score": round(market_score, 1),
            "regime": dominant_regime,
            "warnings": warnings,
            "trend_analysis": trend_analysis,
            "options_analysis": {k: v.get('sentiment') for k, v in options_analysis.items()},
            "gex": {k: round(v, 2) if v is not None else None for k, v in gex_analysis.items()},
            "regimes": {k: v.get('regime') for k, v in (regime_analysis or {}).items()},
            "yield_curve": intermarket_analysis['yield_curve']['status']
        }
        
        return final_analysis 