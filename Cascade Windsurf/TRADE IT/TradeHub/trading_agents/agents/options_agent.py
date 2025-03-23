"""
Options Expert Agent - Analyzes options flow and unusual options activity.
This agent examines options volume, open interest, implied volatility,
and other options-related data to identify potential directional biases.
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentState

class OptionsSignal(BaseModel):
    """Model for an options signal."""
    ticker: str
    timestamp: str
    signal_type: str  # "unusual_volume", "iv_spike", "skew_change", etc.
    expiration: str
    strike: float
    option_type: str  # "call" or "put"
    volume: int
    open_interest: int
    volume_oi_ratio: float
    implied_volatility: float
    direction: int  # 1 for bullish, -1 for bearish, 0 for neutral
    strength: float  # 0.0 to 1.0
    notes: str = ""

class OptionsAnalysis(BaseModel):
    """Model for options analysis data."""
    ticker: str
    timestamp: str
    signals: List[OptionsSignal] = []
    call_put_ratio: float = 1.0
    iv_percentile: float = 0.5
    term_structure: Dict[str, float] = {}
    skew: Dict[str, float] = {}
    analysis: Dict[str, Any] = {}

class OptionsExpertAgent(BaseAgent):
    """
    Agent responsible for analyzing options flow and unusual options activity.
    This agent examines options volume, open interest, implied volatility,
    and other options-related data to identify potential directional biases.
    """
    
    def __init__(self, agent_id: str = "options_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the Options Expert Agent."""
        super().__init__(agent_id, config or {})
        config = config or {}
        self.volume_threshold = config.get("volume_threshold", 3.0)  # Multiple of average volume
        self.open_interest_ratio = config.get("open_interest_ratio", 1.5)  # Volume to OI ratio
    
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
    
    async def process(self, data: Dict[str, Any]) -> OptionsAnalysis:
        """
        Process options data to identify unusual activity and directional biases.
        
        This method analyzes options volume, open interest, implied volatility,
        and other options-related data to identify potential trading signals.
        """
        ticker = data["ticker"]
        volume_threshold = data.get("volume_threshold", self.volume_threshold)
        open_interest_ratio = data.get("open_interest_ratio", self.open_interest_ratio)
        
        logger.info(f"Analyzing options data for {ticker}")
        
        # In a real implementation, this would fetch actual options data
        # For this example, we'll simulate options analysis
        
        # Simulate options chain data
        options_chain = self._simulate_options_chain(ticker)
        
        # Calculate call/put ratio
        call_put_ratio = self._calculate_call_put_ratio(options_chain)
        
        # Calculate IV percentile
        iv_percentile = self._calculate_iv_percentile(ticker)
        
        # Analyze term structure
        term_structure = self._analyze_term_structure(ticker)
        
        # Analyze skew
        skew = self._analyze_skew(ticker)
        
        # Identify unusual options activity
        signals = self._identify_unusual_activity(
            ticker, options_chain, volume_threshold, open_interest_ratio
        )
        
        # Create options analysis result
        result = OptionsAnalysis(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            signals=signals,
            call_put_ratio=call_put_ratio,
            iv_percentile=iv_percentile,
            term_structure=term_structure,
            skew=skew,
            analysis={
                "overall_bias": self._determine_overall_bias(signals, call_put_ratio, skew),
                "iv_regime": "high" if iv_percentile > 0.7 else "low" if iv_percentile < 0.3 else "normal",
                "term_structure_shape": "contango" if list(term_structure.values())[-1] > list(term_structure.values())[0] else "backwardation",
                "notes": self._generate_analysis_notes(signals, call_put_ratio, iv_percentile, skew)
            }
        )
        
        logger.info(f"Options analysis for {ticker}: found {len(signals)} unusual activity signals")
        
        return result
    
    def _simulate_options_chain(self, ticker: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Simulate options chain data.
        
        In a real implementation, this would fetch actual options chain data.
        """
        # Generate random options chain for simulation
        # In a real implementation, this would use actual market data
        
        # Current price (simulated)
        current_price = 100.0 + np.random.uniform(-20, 20)
        
        # Generate expiration dates
        today = datetime.now()
        expirations = [
            (today + timedelta(days=7)).strftime("%Y-%m-%d"),   # 1 week
            (today + timedelta(days=30)).strftime("%Y-%m-%d"),  # 1 month
            (today + timedelta(days=90)).strftime("%Y-%m-%d"),  # 3 months
            (today + timedelta(days=180)).strftime("%Y-%m-%d"), # 6 months
        ]
        
        options_chain = {}
        
        for expiration in expirations:
            options = []
            
            # Generate strikes around current price
            for strike_offset in np.arange(-0.3, 0.31, 0.05):
                strike = current_price * (1 + strike_offset)
                
                # Generate call option
                call = {
                    "strike": strike,
                    "option_type": "call",
                    "expiration": expiration,
                    "volume": int(np.random.exponential(500) if np.random.random() < 0.1 else np.random.exponential(50)),
                    "open_interest": int(np.random.exponential(1000)),
                    "implied_volatility": max(0.1, min(2.0, np.random.normal(0.3, 0.1))),
                    "delta": max(0, min(1, 0.5 + strike_offset * -3)),
                    "gamma": max(0, np.random.normal(0.05, 0.02)),
                    "theta": np.random.normal(-0.02, 0.01),
                    "vega": np.random.normal(0.1, 0.05),
                }
                
                # Generate put option
                put = {
                    "strike": strike,
                    "option_type": "put",
                    "expiration": expiration,
                    "volume": int(np.random.exponential(500) if np.random.random() < 0.1 else np.random.exponential(50)),
                    "open_interest": int(np.random.exponential(1000)),
                    "implied_volatility": max(0.1, min(2.0, np.random.normal(0.3, 0.1))),
                    "delta": max(-1, min(0, -0.5 + strike_offset * 3)),
                    "gamma": max(0, np.random.normal(0.05, 0.02)),
                    "theta": np.random.normal(-0.02, 0.01),
                    "vega": np.random.normal(0.1, 0.05),
                }
                
                options.extend([call, put])
            
            options_chain[expiration] = options
        
        return options_chain
    
    def _calculate_call_put_ratio(self, options_chain: Dict[str, List[Dict[str, Any]]]) -> float:
        """
        Calculate the call/put ratio based on volume.
        
        A ratio > 1 indicates more call volume (potentially bullish).
        A ratio < 1 indicates more put volume (potentially bearish).
        """
        total_call_volume = 0
        total_put_volume = 0
        
        for expiration, options in options_chain.items():
            for option in options:
                if option["option_type"] == "call":
                    total_call_volume += option["volume"]
                else:
                    total_put_volume += option["volume"]
        
        if total_put_volume == 0:
            return 5.0  # Cap at 5.0 if no put volume
        
        return min(5.0, total_call_volume / total_put_volume)
    
    def _calculate_iv_percentile(self, ticker: str) -> float:
        """
        Calculate the implied volatility percentile.
        
        In a real implementation, this would compare current IV to historical IV.
        Returns a value between 0.0 (low IV) and 1.0 (high IV).
        """
        # Simulate IV percentile for demonstration
        return np.random.uniform(0, 1)
    
    def _analyze_term_structure(self, ticker: str) -> Dict[str, float]:
        """
        Analyze the volatility term structure.
        
        In a real implementation, this would analyze IV across different expirations.
        Returns a dictionary mapping expiration to IV.
        """
        # Simulate term structure for demonstration
        today = datetime.now()
        expirations = [
            (today + timedelta(days=7)).strftime("%Y-%m-%d"),   # 1 week
            (today + timedelta(days=30)).strftime("%Y-%m-%d"),  # 1 month
            (today + timedelta(days=90)).strftime("%Y-%m-%d"),  # 3 months
            (today + timedelta(days=180)).strftime("%Y-%m-%d"), # 6 months
        ]
        
        # Generate random term structure (usually upward sloping)
        base_iv = np.random.uniform(0.2, 0.5)
        term_structure = {}
        
        for i, expiration in enumerate(expirations):
            # Add some randomness to the term structure
            if np.random.random() < 0.7:  # 70% chance of upward sloping
                term_structure[expiration] = base_iv * (1 + i * 0.1 * np.random.uniform(0.8, 1.2))
            else:  # 30% chance of downward sloping (backwardation)
                term_structure[expiration] = base_iv * (1 - i * 0.05 * np.random.uniform(0.8, 1.2))
        
        return term_structure
    
    def _analyze_skew(self, ticker: str) -> Dict[str, float]:
        """
        Analyze the volatility skew.
        
        In a real implementation, this would analyze IV across different strikes.
        Returns a dictionary with skew metrics.
        """
        # Simulate skew for demonstration
        
        # Generate random skew metrics
        put_call_skew = np.random.normal(1.1, 0.2)  # Typically puts have higher IV
        wing_steepness = np.random.uniform(0.5, 2.0)
        atm_iv = np.random.uniform(0.2, 0.5)
        
        return {
            "put_call_skew": put_call_skew,
            "wing_steepness": wing_steepness,
            "atm_iv": atm_iv,
            "25_delta_skew": put_call_skew * wing_steepness,
            "10_delta_skew": put_call_skew * wing_steepness * 1.5
        }
    
    def _identify_unusual_activity(
        self, 
        ticker: str, 
        options_chain: Dict[str, List[Dict[str, Any]]],
        volume_threshold: float,
        open_interest_ratio: float
    ) -> List[OptionsSignal]:
        """
        Identify unusual options activity.
        
        This method looks for options with unusually high volume relative to open interest,
        unusual implied volatility changes, or other notable patterns.
        """
        signals = []
        
        for expiration, options in options_chain.items():
            for option in options:
                # Check for unusual volume
                volume_oi_ratio = option["volume"] / max(1, option["open_interest"])
                
                if volume_oi_ratio > open_interest_ratio and option["volume"] > 100:
                    # Determine direction based on option type and delta
                    if option["option_type"] == "call":
                        direction = 1  # Bullish
                    else:
                        direction = -1  # Bearish
                    
                    # Calculate signal strength based on volume and ratio
                    strength = min(1.0, (volume_oi_ratio / open_interest_ratio) * 0.5 + (option["volume"] / 1000) * 0.5)
                    
                    # Create signal
                    signal = OptionsSignal(
                        ticker=ticker,
                        timestamp=datetime.now().isoformat(),
                        signal_type="unusual_volume",
                        expiration=expiration,
                        strike=option["strike"],
                        option_type=option["option_type"],
                        volume=option["volume"],
                        open_interest=option["open_interest"],
                        volume_oi_ratio=volume_oi_ratio,
                        implied_volatility=option["implied_volatility"],
                        direction=direction,
                        strength=strength,
                        notes=f"Unusual {option['option_type']} volume at strike {option['strike']}"
                    )
                    
                    signals.append(signal)
                
                # Check for unusual IV (simplified for demonstration)
                if option["implied_volatility"] > 0.5 and option["volume"] > 50:
                    # Determine direction based on option type and IV change
                    if option["option_type"] == "call":
                        direction = 1  # Bullish
                    else:
                        direction = -1  # Bearish
                    
                    # Calculate signal strength based on IV
                    strength = min(1.0, option["implied_volatility"] * 0.7)
                    
                    # Create signal
                    signal = OptionsSignal(
                        ticker=ticker,
                        timestamp=datetime.now().isoformat(),
                        signal_type="iv_spike",
                        expiration=expiration,
                        strike=option["strike"],
                        option_type=option["option_type"],
                        volume=option["volume"],
                        open_interest=option["open_interest"],
                        volume_oi_ratio=volume_oi_ratio,
                        implied_volatility=option["implied_volatility"],
                        direction=direction,
                        strength=strength,
                        notes=f"High IV ({option['implied_volatility']:.2f}) on {option['option_type']} at strike {option['strike']}"
                    )
                    
                    signals.append(signal)
        
        return signals
    
    def _determine_overall_bias(
        self, signals: List[OptionsSignal], call_put_ratio: float, skew: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Determine the overall directional bias based on options data.
        """
        # Calculate weighted direction from signals
        if signals:
            weighted_direction = sum(signal.direction * signal.strength for signal in signals) / len(signals)
        else:
            weighted_direction = 0
        
        # Factor in call/put ratio (normalize to -1 to 1 scale)
        cp_bias = min(1, max(-1, (call_put_ratio - 1) * 0.5))
        
        # Factor in skew (put/call skew > 1 is typically bearish)
        skew_bias = min(1, max(-1, (1 - skew["put_call_skew"]) * 2))
        
        # Calculate overall bias
        overall_bias = 0.5 * weighted_direction + 0.3 * cp_bias + 0.2 * skew_bias
        
        # Determine direction and strength
        if overall_bias > 0.2:
            direction = "bullish"
            strength = min(1.0, overall_bias * 2)
        elif overall_bias < -0.2:
            direction = "bearish"
            strength = min(1.0, abs(overall_bias) * 2)
        else:
            direction = "neutral"
            strength = min(1.0, (1 - abs(overall_bias * 5)))
        
        return {
            "direction": direction,
            "strength": strength,
            "score": overall_bias,
            "components": {
                "signals_bias": weighted_direction,
                "call_put_ratio_bias": cp_bias,
                "skew_bias": skew_bias
            }
        }
    
    def _generate_analysis_notes(
        self, signals: List[OptionsSignal], call_put_ratio: float, iv_percentile: float, skew: Dict[str, float]
    ) -> str:
        """Generate analysis notes based on options data."""
        notes = []
        
        # Signal notes
        if signals:
            bullish_signals = sum(1 for s in signals if s.direction > 0)
            bearish_signals = sum(1 for s in signals if s.direction < 0)
            notes.append(f"Found {len(signals)} unusual activity signals ({bullish_signals} bullish, {bearish_signals} bearish)")
        else:
            notes.append("No unusual options activity detected")
        
        # Call/put ratio notes
        if call_put_ratio > 1.5:
            notes.append(f"Bullish call/put ratio: {call_put_ratio:.2f}")
        elif call_put_ratio < 0.7:
            notes.append(f"Bearish call/put ratio: {call_put_ratio:.2f}")
        else:
            notes.append(f"Neutral call/put ratio: {call_put_ratio:.2f}")
        
        # IV notes
        if iv_percentile > 0.7:
            notes.append(f"High implied volatility (percentile: {iv_percentile:.2f})")
        elif iv_percentile < 0.3:
            notes.append(f"Low implied volatility (percentile: {iv_percentile:.2f})")
        else:
            notes.append(f"Normal implied volatility (percentile: {iv_percentile:.2f})")
        
        # Skew notes
        if skew["put_call_skew"] > 1.2:
            notes.append(f"Steep put skew (ratio: {skew['put_call_skew']:.2f})")
        elif skew["put_call_skew"] < 0.9:
            notes.append(f"Inverted skew (ratio: {skew['put_call_skew']:.2f})")
        else:
            notes.append(f"Normal volatility skew (ratio: {skew['put_call_skew']:.2f})")
        
        return " | ".join(notes) 