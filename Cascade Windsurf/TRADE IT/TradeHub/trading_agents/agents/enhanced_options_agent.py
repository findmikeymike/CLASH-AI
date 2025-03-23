"""
Enhanced Options Expert Agent - Analyzes options flow, unusual activity, GEX levels,
and detects stop hunt patterns in both directions.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from enum import Enum
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentState

class Direction(Enum):
    """Direction enum for indicating bullish, bearish, or neutral sentiment."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

class EnhancedOptionsExpertAgent(BaseAgent):
    """
    Enhanced Options Expert Agent that analyzes options data to identify unusual activity,
    detect stop hunts, and analyze gamma exposure (GEX) levels.
    """
    
    def __init__(self, volume_threshold=2.0, open_interest_ratio=1.5, stop_hunt_sensitivity=0.5):
        """
        Initialize the EnhancedOptionsExpertAgent.
        
        Args:
            volume_threshold: Threshold for unusual volume (multiple of average)
            open_interest_ratio: Threshold for unusual open interest (multiple of average)
            stop_hunt_sensitivity: Sensitivity for stop hunt detection (0.0-1.0)
        """
        super().__init__(agent_id="enhanced_options_agent")
        
        # Store configuration
        self.volume_threshold = volume_threshold
        self.open_interest_ratio = open_interest_ratio
        
        logger.info(f"Enhanced Options Expert Agent initialized with volume_threshold={volume_threshold}, open_interest_ratio={open_interest_ratio}")
        
        # Initialize stop hunt detector
        self.stop_hunt_detector = BidirectionalStopHuntDetector(sensitivity=stop_hunt_sensitivity)
        
        # Initialize GEX analyzer
        self.gex_analyzer = GEXAnalyzer()
    
    async def validate(self, data: Any) -> bool:
        """Validate input data."""
        if not isinstance(data, dict):
            logger.error("Input data must be a dictionary")
            return False
        
        required_fields = ["ticker"]
        if not all(field in data for field in required_fields):
            logger.error(f"Missing required fields: {required_fields}")
            return False
        
        return True
    
    def process(self, data):
        """
        Process options data to identify unusual activity and generate analysis.
        
        Args:
            data: Dictionary containing ticker and price data
            
        Returns:
            Dictionary with analysis results
        """
        ticker = data.get('ticker', '')
        price_data = data.get('price_data')
        
        logger.info(f"Analyzing options data for {ticker}")
        
        # Fetch options data
        options_chain = self._fetch_options_chain(ticker)
        historical_data = self._fetch_historical_options_data(ticker)
        order_flow_data = self._fetch_order_flow_data(ticker)
        
        # Analyze options data
        options_analysis = self._analyze_options_data(
            options_chain,
            price_data,
            historical_data
        )
        
        # Detect unusual activity
        unusual_activity = self._detect_unusual_activity(
            options_chain,
            historical_data
        )
        
        # Analyze sweep activity
        sweep_activity = self._analyze_sweep_activity(order_flow_data)
        
        # Analyze GEX levels
        gex_analysis = self.gex_analyzer.analyze(
            options_chain,
            price_data,
            historical_data
        )
        
        # Detect stop hunts
        stop_hunt_results = self.stop_hunt_detector.detect(
            options_chain,
            price_data,
            order_flow_data
        )
        
        # Generate consolidated output
        result = self._generate_consolidated_output(
            ticker,
            options_analysis,
            unusual_activity,
            sweep_activity,
            gex_analysis,
            stop_hunt_results
        )
        
        logger.info(f"Enhanced options analysis for {ticker} complete")
        return result
    
    def _fetch_options_chain(self, ticker):
        """Fetch options chain for the given ticker."""
        logger.info(f"Fetching options chain for {ticker}")
        # This is a simplified implementation
        # In a real implementation, this would fetch the options chain from a data provider
        
        # For now, return a DataFrame with random data
        return pd.DataFrame({
            'strike': np.linspace(90, 110, 21),
            'call_volume': np.random.randint(10, 1000, 21),
            'put_volume': np.random.randint(10, 1000, 21),
            'call_oi': np.random.randint(100, 10000, 21),
            'put_oi': np.random.randint(100, 10000, 21),
            'call_iv': np.random.uniform(0.2, 0.6, 21),
            'put_iv': np.random.uniform(0.2, 0.6, 21),
            'call_delta': np.linspace(0.9, 0.1, 21),
            'put_delta': np.linspace(-0.1, -0.9, 21),
            'call_gamma': np.random.uniform(0.01, 0.1, 21),
            'put_gamma': np.random.uniform(0.01, 0.1, 21)
        })
    
    def _fetch_historical_options_data(self, ticker):
        """Fetch historical options data for the given ticker."""
        logger.info(f"Fetching historical options data for {ticker}")
        # This is a simplified implementation
        # In a real implementation, this would fetch historical options data from a data provider
        
        # For now, return a DataFrame with random data
        return pd.DataFrame({
            'date': pd.date_range(end=pd.Timestamp.now(), periods=30),
            'call_volume': np.random.randint(10000, 100000, 30),
            'put_volume': np.random.randint(10000, 100000, 30),
            'call_oi': np.random.randint(100000, 1000000, 30),
            'put_oi': np.random.randint(100000, 1000000, 30),
            'call_put_ratio': np.random.uniform(0.5, 2.0, 30),
            'avg_iv': np.random.uniform(0.2, 0.6, 30)
        })
    
    def _fetch_order_flow_data(self, ticker):
        """Fetch options order flow data for the given ticker."""
        logger.info(f"Fetching order flow data for {ticker}")
        # This is a simplified implementation
        # In a real implementation, this would fetch options order flow data from a data provider
        
        # For now, return a DataFrame with random data
        return pd.DataFrame({
            'timestamp': pd.date_range(end=pd.Timestamp.now(), periods=50, freq='15min'),
            'contract': [f"{np.random.choice(['CALL', 'PUT'])} {np.random.randint(90, 110)} {pd.Timestamp.now().strftime('%Y-%m-%d')}" for _ in range(50)],
            'size': np.random.randint(10, 1000, 50),
            'price': np.random.uniform(0.5, 10.0, 50),
            'type': np.random.choice(['sweep', 'block', 'split', 'regular'], 50),
            'side': np.random.choice(['buy', 'sell'], 50),
            'exchange': np.random.choice(['CBOE', 'AMEX', 'PHLX', 'ISE'], 50)
        })
    
    def _analyze_options_data(self, options_chain, price_data, historical_data):
        """Analyze options data to identify patterns and generate signals."""
        # This is a simplified implementation
        # In a real implementation, this would analyze the options data in detail
        
        # For now, return a dictionary with random data
        signals = []
        
        # Add some random signals
        if np.random.random() < 0.7:  # 70% chance of having signals
            num_signals = np.random.randint(1, 5)
            signal_types = ['unusual_volume', 'iv_spike', 'skew_change', 'oi_increase', 'oi_decrease']
            directions = ['bullish', 'bearish', 'neutral']
            
            for _ in range(num_signals):
                signals.append({
                    'type': np.random.choice(signal_types),
                    'direction': np.random.choice(directions),
                    'strength': np.random.uniform(0.5, 1.0),
                    'description': f"Signal description {_+1}"
                })
        
        # Determine overall sentiment based on signals
        if not signals:
            overall_sentiment = 'neutral'
            confidence = 'low'
        else:
            # Count bullish and bearish signals
            bullish_count = sum(1 for s in signals if s['direction'] == 'bullish')
            bearish_count = sum(1 for s in signals if s['direction'] == 'bearish')
            
            if bullish_count > bearish_count:
                overall_sentiment = 'bullish'
            elif bearish_count > bullish_count:
                overall_sentiment = 'bearish'
            else:
                overall_sentiment = 'neutral'
            
            # Determine confidence based on signal strength
            avg_strength = sum(s['strength'] for s in signals) / len(signals)
            if avg_strength > 0.8:
                confidence = 'high'
            elif avg_strength > 0.5:
                confidence = 'medium'
            else:
                confidence = 'low'
        
        return {
            'signals': signals,
            'overall_sentiment': overall_sentiment,
            'confidence': confidence
        }
    
    def _detect_unusual_activity(self, options_chain, historical_data):
        """Detect unusual options activity based on volume, OI, and IV."""
        # This is a simplified implementation
        # In a real implementation, this would analyze the options data in detail
        
        # For now, return a dictionary with random data
        call_put_ratio = np.random.uniform(0.3, 2.0)
        iv_percentile = np.random.uniform(0.0, 1.0)
        skew = np.random.uniform(-0.2, 0.2)
        
        # Determine sentiment based on call/put ratio and skew
        if call_put_ratio > 1.5 and skew > 0.1:
            sentiment = 'strongly_bullish'
        elif call_put_ratio > 1.2:
            sentiment = 'bullish'
        elif call_put_ratio < 0.5 and skew < -0.1:
            sentiment = 'strongly_bearish'
        elif call_put_ratio < 0.8:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'
        
        return {
            'call_put_ratio': call_put_ratio,
            'iv_percentile': iv_percentile,
            'skew': skew,
            'sentiment': sentiment
        }
    
    def _analyze_sweep_activity(self, order_flow_data):
        """Analyze options sweep activity to identify directional bias."""
        # This is a simplified implementation
        # In a real implementation, this would analyze the order flow data in detail
        
        # For now, return a dictionary with random data
        call_sweep_volume = np.random.randint(100, 2000)
        put_sweep_volume = np.random.randint(100, 2000)
        
        # Determine sentiment based on sweep volume
        if call_sweep_volume > put_sweep_volume * 2:
            sweep_sentiment = 'strongly_bullish'
        elif call_sweep_volume > put_sweep_volume * 1.3:
            sweep_sentiment = 'bullish'
        elif put_sweep_volume > call_sweep_volume * 2:
            sweep_sentiment = 'strongly_bearish'
        elif put_sweep_volume > call_sweep_volume * 1.3:
            sweep_sentiment = 'bearish'
        else:
            sweep_sentiment = 'neutral'
        
        return {
            'call_sweep_volume': call_sweep_volume,
            'put_sweep_volume': put_sweep_volume,
            'sweep_sentiment': sweep_sentiment
        }
    
    def _generate_consolidated_output(self, ticker, options_analysis, unusual_activity, sweep_activity, gex_analysis, stop_hunt_results):
        """Generate consolidated output with all analysis results."""
        # Determine overall sentiment
        sentiment = options_analysis.get('overall_sentiment', 'neutral')
        confidence = options_analysis.get('confidence', 'medium')
        
        # Compile risk warnings
        risk_warnings = []
        
        # Add GEX-related warnings
        if gex_analysis.get('gex_wall_proximity') and gex_analysis['gex_wall_proximity'].get('is_near'):
            risk_warnings.append(
                f"Price approaching {gex_analysis['gex_wall_proximity']['direction']} GEX wall at ${gex_analysis['gex_wall_proximity']['wall_price']:.2f} "
                f"({gex_analysis['gex_wall_proximity']['distance_pct']*100:.1f}% away)"
            )
            
        if gex_analysis.get('gex_weakness') and gex_analysis.get('gex_weakness_direction'):
            risk_warnings.append(
                f"GEX weakness detected, potential for rapid {gex_analysis['gex_weakness_direction']} move"
            )
            
        if gex_analysis.get('gex_inflection_point') and gex_analysis.get('gex_inflection_level'):
            risk_warnings.append(
                f"GEX inflection point detected at ${gex_analysis['gex_inflection_level']:.2f}"
            )
        
        # Add stop hunt warnings
        if stop_hunt_results.get('has_stop_hunt'):
            if stop_hunt_results.get('upward_stop_hunt', {}).get('detected'):
                risk_warnings.append("Potential upward stop hunt detected")
                
            if stop_hunt_results.get('downward_stop_hunt', {}).get('detected'):
                risk_warnings.append("Potential downward stop hunt detected")
                
            risk_warnings.append(f"Stop hunt risk level: {stop_hunt_results.get('risk_level', 'medium')}")
        
        # Generate recommended contracts
        recommended_contracts = self._generate_recommended_contracts(options_analysis, unusual_activity)
        
        # Determine recommended strategy
        recommended_strategy = self._determine_recommended_strategy(
            sentiment, 
            unusual_activity, 
            sweep_activity,
            gex_analysis
        )
        
        # Compile final result
        result = {
            'ticker': ticker,
            'options_analysis': {
                'sentiment': sentiment,
                'confidence': confidence,
                'call_put_ratio': unusual_activity.get('call_put_ratio', 0),
                'iv_percentile': unusual_activity.get('iv_percentile', 0),
                'skew': unusual_activity.get('skew', 0),
                'signals': options_analysis.get('signals', [])
            },
            'unusual_activity': unusual_activity,
            'sweep_activity': sweep_activity,
            'gex_analysis': gex_analysis,
            'risk_warnings': risk_warnings,
            'stop_hunt_warnings': stop_hunt_results,
            'recommended_contracts': recommended_contracts,
            'recommended_strategy': recommended_strategy
        }
        
        return result
    
    def _generate_recommended_contracts(self, options_analysis, unusual_activity):
        """Generate recommended option contracts based on analysis."""
        # This is a simplified implementation
        # In a real implementation, we would select contracts based on the analysis
        
        # For now, return a few sample contracts
        return [
            {
                'type': 'CALL',
                'strike': 100,
                'expiration': '2023-06-16',
                'iv': 0.30,
                'delta': 0.50
            },
            {
                'type': 'CALL',
                'strike': 105,
                'expiration': '2023-06-16',
                'iv': 0.32,
                'delta': 0.40
            },
            {
                'type': 'PUT',
                'strike': 95,
                'expiration': '2023-06-16',
                'iv': 0.35,
                'delta': -0.40
            }
        ]
    
    def _determine_recommended_strategy(self, sentiment, unusual_activity, sweep_activity, gex_analysis):
        """Determine recommended options strategy based on analysis."""
        # This is a simplified implementation
        # In a real implementation, we would determine the strategy based on the analysis
        
        # For now, randomly select a strategy based on sentiment
        if sentiment == 'bullish' or sentiment == 'strongly_bullish':
            return np.random.choice(['call_spread', 'call_backspread', 'risk_reversal'])
        elif sentiment == 'bearish' or sentiment == 'strongly_bearish':
            return np.random.choice(['put_spread', 'put_backspread', 'collar'])
        else:
            return np.random.choice(['iron_condor', 'butterfly', 'calendar_spread'])


class BidirectionalStopHuntDetector:
    """
    Detects potential stop hunt patterns in both directions where large options positions
    paradoxically cause short-term counter-trend price movements due to market maker hedging.
    """
    
    def __init__(self, sensitivity=0.7):
        """
        Initialize the stop hunt detector.
        
        Args:
            sensitivity (float): Value between 0-1 adjusting detection sensitivity
        """
        self.sensitivity = sensitivity
        logger.info(f"BidirectionalStopHuntDetector initialized with sensitivity={sensitivity}")
        
    def detect(self, options_data, price_data, order_flow_data):
        """
        Detect potential stop hunts in both directions.
        
        Args:
            options_data: DataFrame containing options chain data
            price_data: DataFrame containing price history
            order_flow_data: DataFrame containing options order flow data
            
        Returns:
            Dictionary with stop hunt analysis results
        """
        # Check if we have valid data
        if options_data is None or options_data.empty:
            logger.warning("No options data available for stop hunt detection")
            return self._empty_result()
            
        # For price data, we'll use a default current price if it's None
        current_price = 100.0  # Default value
        if price_data is not None and not price_data.empty:
            current_price = price_data.iloc[-1]['Close']
            
        # For order flow, we'll proceed without it if it's None
        has_order_flow = order_flow_data is not None and not order_flow_data.empty
        
        # This is a simplified implementation
        # In a real implementation, we would analyze price action, options activity,
        # and order flow to detect potential stop hunts
        
        # For now, randomly determine if there's a stop hunt
        upward_stop_hunt = self._detect_upward_stop_hunt(current_price)
        downward_stop_hunt = self._detect_downward_stop_hunt(current_price)
        
        return {
            'upward_stop_hunt': upward_stop_hunt,
            'downward_stop_hunt': downward_stop_hunt,
            'has_stop_hunt': upward_stop_hunt['detected'] or downward_stop_hunt['detected'],
            'risk_level': self._calculate_risk_level(upward_stop_hunt, downward_stop_hunt)
        }
    
    def _empty_result(self):
        """Return an empty result when analysis cannot be performed."""
        return {
            'upward_stop_hunt': {'detected': False},
            'downward_stop_hunt': {'detected': False},
            'has_stop_hunt': False,
            'risk_level': 'low'
        }
    
    def _detect_upward_stop_hunt(self, current_price):
        """Detect upward stop hunt."""
        # This is a simplified implementation
        # In a real implementation, this would analyze price action and options activity
        
        # For now, randomly determine if there's an upward stop hunt
        if np.random.random() < 0.3:  # 30% chance of detecting an upward stop hunt
            return {'detected': True}
        
        return {'detected': False}
    
    def _detect_downward_stop_hunt(self, current_price):
        """Detect downward stop hunt."""
        # This is a simplified implementation
        # In a real implementation, this would analyze price action and options activity
        
        # For now, randomly determine if there's a downward stop hunt
        if np.random.random() < 0.3:  # 30% chance of detecting a downward stop hunt
            return {'detected': True}
        
        return {'detected': False}
    
    def _calculate_risk_level(self, upward_stop_hunt, downward_stop_hunt):
        """Calculate risk level based on detected stop hunts."""
        # This is a simplified implementation
        # In a real implementation, this would calculate a risk level based on the detected stop hunts
        
        # For now, return a fixed risk level
        return 'medium'


class GEXAnalyzer:
    """
    Analyzes Gamma Exposure (GEX) levels to identify potential support/resistance,
    price walls, and areas where price movement might accelerate due to lack of gamma.
    """
    
    def __init__(self):
        """Initialize the GEX analyzer."""
        logger.info("GEXAnalyzer initialized")
    
    def analyze(self, options_data: pd.DataFrame, price_data: Optional[pd.DataFrame], historical_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Analyze GEX levels to identify potential support/resistance, price walls, and areas where price movement might accelerate.
        
        Args:
            options_data: DataFrame containing options chain data
            price_data: DataFrame containing price history
            historical_data: Optional DataFrame containing historical options data
            
        Returns:
            Dictionary with GEX analysis results
        """
        logger.info("Analyzing GEX levels")
        
        # Check if options data is empty
        if options_data.empty:
            logger.warning("Options data is empty, cannot perform GEX analysis")
            return self._empty_result()
        
        # Get current price from price data or use a default
        current_price = 100.0  # Default value
        if price_data is not None and not price_data.empty and 'close' in price_data.columns:
            current_price = price_data['close'].iloc[-1]
        
        # Calculate GEX per strike
        gex_per_strike = self._calculate_gex_per_strike(options_data)
        
        # Calculate total GEX
        total_gex = self._calculate_total_gex(gex_per_strike)
        
        # Calculate GEX skew
        gex_skew = self._calculate_gex_skew(gex_per_strike, current_price)
        
        # Identify significant GEX levels
        gex_levels = self._identify_gex_levels(gex_per_strike, current_price)
        
        # Find largest GEX level
        largest_gex_level = max(gex_levels, key=lambda x: abs(x['gex'])) if gex_levels else None
        
        # Find next GEX level
        next_gex_level = self._find_next_gex_level(gex_levels, current_price) if gex_levels else None
        
        # Detect GEX walls
        gex_walls = self._identify_gex_walls(gex_per_strike, current_price)
        
        # Check for GEX wall proximity
        gex_wall_proximity = self._check_gex_wall_proximity(gex_walls, current_price) if gex_walls else None
        
        # Detect GEX weakness
        gex_weakness, gex_weakness_direction = self._detect_gex_weakness(gex_per_strike, current_price)
        
        # Detect GEX inflection points
        gex_inflection_point, gex_inflection_level = self._detect_gex_inflection_points(gex_per_strike, current_price)
        
        # Determine GEX support/resistance
        gex_support_resistance = self._determine_gex_support_resistance(gex_per_strike, current_price)
        
        return {
            "current_gex": total_gex,
            "gex_skew": gex_skew,
            "gex_levels": gex_levels,
            "largest_gex_level": largest_gex_level['price'] if largest_gex_level else None,
            "next_gex_level": next_gex_level,
            "gex_walls": gex_walls,
            "gex_wall_proximity": gex_wall_proximity,
            "gex_weakness": gex_weakness,
            "gex_weakness_direction": gex_weakness_direction if gex_weakness else None,
            "gex_inflection_point": gex_inflection_point,
            "gex_inflection_level": gex_inflection_level,
            "gex_support_resistance": gex_support_resistance
        }
    
    def _empty_result(self):
        """Return an empty result when analysis cannot be performed."""
        return {
            'current_gex': 0,
            'gex_skew': 0,
            'gex_levels': [],
            'largest_gex_level': None,
            'next_gex_level': None,
            'gex_walls': None,
            'gex_wall_proximity': None,
            'gex_weakness': False,
            'gex_weakness_direction': None,
            'gex_inflection_point': False,
            'gex_inflection_level': None,
            'gex_support_resistance': None
        }
    
    def _calculate_gex_per_strike(self, options_data):
        """Calculate GEX per strike price."""
        # This is a simplified implementation
        # In a real implementation, this would calculate gamma exposure at each strike
        
        # For now, generate random GEX values
        strikes = np.linspace(90, 110, 21)  # Generate 21 strikes from 90 to 110
        
        return {
            'strikes': strikes,
            'call_gex': np.random.normal(0, 1000, size=len(strikes)),
            'put_gex': np.random.normal(0, 1000, size=len(strikes)) * -1,  # Make puts negative after generation
            'total_gex': np.random.normal(0, 1500, size=len(strikes))
        }
    
    def _calculate_total_gex(self, gex_per_strike):
        """Calculate total GEX across all strikes."""
        # This is a simplified implementation
        
        # In a real implementation, we would sum the total GEX across all strikes
        
        # For now, return the sum of the total_gex array
        return np.sum(gex_per_strike['total_gex'])
    
    def _calculate_gex_skew(self, gex_per_strike, current_price):
        """Calculate GEX skew (positive vs negative GEX)."""
        # This is a simplified implementation
        
        # In a real implementation, we would calculate the ratio of positive to negative GEX
        
        # For now, return a random skew value
        return np.random.uniform(-1.0, 1.0)
    
    def _identify_gex_levels(self, gex_per_strike, current_price):
        """Identify significant GEX levels."""
        # This is a simplified implementation
        
        # In a real implementation, we would identify strikes with significant GEX
        
        # For now, randomly select a few strikes as significant GEX levels
        strikes = gex_per_strike['strikes']
        total_gex = gex_per_strike['total_gex']
        
        # Get indices of the 3 strikes with the highest absolute GEX values
        indices = np.argsort(np.abs(total_gex))[-3:]
        
        gex_levels = []
        for idx in indices:
            gex_levels.append({
                'price': strikes[idx],
                'gex': total_gex[idx],
                'distance_pct': (strikes[idx] - current_price) / current_price
            })
        
        return gex_levels
    
    def _find_next_gex_level(self, gex_levels, current_price):
        """Find the next GEX level in the current price direction."""
        if not gex_levels:
            return None
        
        # Sort levels by distance from current price
        levels_by_distance = sorted(gex_levels, key=lambda x: abs(x['price'] - current_price))
        
        # Return the price of the next level
        return levels_by_distance[0]['price'] if levels_by_distance else None
    
    def _identify_gex_walls(self, gex_per_strike, current_price):
        """Identify GEX walls that might act as price barriers."""
        # This is a simplified implementation
        
        # In a real implementation, we would identify areas with concentrated GEX
        
        # For now, randomly determine if there's a GEX wall
        if np.random.random() < 0.4:  # 40% chance of detecting a wall
            wall_direction = np.random.choice(['above', 'below'])
            wall_distance = np.random.uniform(0.01, 0.05)
            wall_price = current_price * (1 + (wall_distance if wall_direction == 'above' else -wall_distance))
            
            return {
                'direction': wall_direction,
                'price': wall_price,
                'strength': np.random.uniform(0.5, 1.0),
                'distance_pct': wall_distance
            }
        
        return None
    
    def _check_gex_wall_proximity(self, gex_walls, current_price):
        """Check if price is near a GEX wall."""
        # This is a simplified implementation
        
        # In a real implementation, we would check the distance to the nearest GEX wall
        
        # For now, if there's a wall, determine if it's close
        if gex_walls:
            distance_pct = gex_walls['distance_pct']
            
            if distance_pct < 0.02:  # If wall is within 2%
                return {
                    'is_near': True,
                    'direction': gex_walls['direction'],
                    'distance_pct': distance_pct,
                    'wall_price': gex_walls['price']
                }
        
        return {
            'is_near': False,
            'direction': None,
            'distance_pct': None,
            'wall_price': None
        }
    
    def _detect_gex_weakness(self, gex_per_strike, current_price):
        """Detect zones of GEX weakness where price might move rapidly."""
        # This is a simplified implementation
        
        # In a real implementation, we would look for areas with low GEX
        # between significant GEX levels, indicating potential for rapid price movement
        
        # For now, randomly determine if there's a weakness
        if np.random.random() < 0.3:  # 30% chance of detecting weakness
            direction = np.random.choice(['upward', 'downward'])
            
            return True, direction
        
        return False, None
    
    def _detect_gex_inflection_points(self, gex_per_strike, current_price):
        """Detect GEX inflection points where GEX changes from positive to negative or vice versa."""
        # This is a simplified implementation
        
        # In a real implementation, we would look for strikes where GEX changes sign
        # from positive to negative or vice versa, indicating potential inflection points
        
        # For now, randomly determine if there's an inflection point
        if np.random.random() < 0.3:  # 30% chance of detecting an inflection point
            inflection_level = current_price * (1 + np.random.uniform(-0.05, 0.05))
            
            return True, inflection_level
        
        return False, None
    
    def _determine_gex_support_resistance(self, gex_per_strike, current_price):
        """Determine if current price is near a GEX support/resistance level."""
        # This is a simplified implementation
        
        # In a real implementation, we would look for nearby strikes with significant GEX
        # and determine if they are likely to act as support or resistance
        
        # For now, randomly determine if there's a support/resistance level
        if np.random.random() < 0.5:  # 50% chance of detecting support/resistance
            level_type = np.random.choice(['support', 'resistance'])
            level_price = current_price * (1 + np.random.uniform(-0.03, 0.03))
            level_strength = np.random.uniform(0.5, 1.0)
            
            return {
                'type': level_type,
                'price': level_price,
                'strength': level_strength,
                'distance_pct': (level_price - current_price) / current_price
            }
        
        return None