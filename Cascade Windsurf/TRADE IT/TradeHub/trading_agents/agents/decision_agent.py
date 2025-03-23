"""
Decision Agent - Makes final trading decisions based on inputs from other agents.
This agent aggregates signals and analysis from multiple specialized agents
to make informed trading decisions with risk management.
"""

from typing import Dict, List, Any, Optional, Union
import numpy as np
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field

from .base_agent import BaseAgent, AgentState

class TradeSignal(BaseModel):
    """Model for a trade signal."""
    ticker: str
    timestamp: str
    signal_type: str  # "entry", "exit", "adjust"
    direction: str  # "long", "short"
    price: float
    confidence: float  # 0.0 to 1.0
    timeframe: str
    source_agent: str
    setup_type: str
    risk_reward: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    notes: str = ""
    metadata: Dict[str, Any] = {}

class TradeDecision(BaseModel):
    """Model for a trade decision."""
    ticker: str
    timestamp: str
    decision: str  # "enter", "exit", "hold", "adjust"
    direction: Optional[str] = None  # "long", "short"
    price: Optional[float] = None
    confidence: float = 0.0
    signals: List[TradeSignal] = []
    risk_reward: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: Optional[float] = None
    timeframe: str = ""
    notes: List[str] = []
    reasoning: str = ""
    metadata: Dict[str, Any] = {}

class RiskParameters(BaseModel):
    """Model for risk management parameters."""
    max_risk_per_trade: float = 0.01  # 1% of account
    max_risk_per_day: float = 0.03  # 3% of account
    max_open_positions: int = 3
    min_risk_reward: float = 2.0
    max_correlated_positions: int = 1
    account_size: float = 10000.0
    position_sizing_method: str = "fixed_risk"  # "fixed_risk", "fixed_size", "kelly"
    default_stop_distance: float = 0.01  # 1% default stop distance

class DecisionAgent(BaseAgent):
    """
    Agent responsible for making final trading decisions.
    
    This agent aggregates signals and analysis from multiple specialized agents
    to make informed trading decisions with risk management.
    """
    
    def __init__(self, agent_id: str = "decision_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the Decision Agent."""
        super().__init__(agent_id, config or {})
        config = config or {}
        
        # Initialize risk parameters
        self.risk_params = RiskParameters(**(config.get("risk_params", {})))
        
        # Track open positions and daily risk
        self.open_positions = {}  # ticker -> position details
        self.daily_risk_used = 0.0
        self.last_reset_date = datetime.now().date()
        
        # Track recent decisions
        self.recent_decisions = []
        self.max_recent_decisions = 100
    
    async def validate(self, data: Any) -> bool:
        """Validate input data."""
        if not isinstance(data, dict):
            logger.error("Input data must be a dictionary")
            return False
        
        required_fields = ["ticker", "signals"]
        if not all(field in data for field in required_fields):
            logger.error(f"Missing required fields: {required_fields}")
            return False
        
        # Validate signals
        signals = data["signals"]
        if not isinstance(signals, list):
            logger.error("Signals must be a list")
            return False
        
        if not signals:
            logger.warning("No signals provided")
            return True  # Empty signals is valid, will result in "hold" decision
        
        # Validate each signal
        for signal in signals:
            if not isinstance(signal, dict) and not isinstance(signal, TradeSignal):
                logger.error("Each signal must be a dictionary or TradeSignal object")
                return False
        
        return True
    
    async def process(self, data: Dict[str, Any]) -> TradeDecision:
        """
        Process signals to make a trading decision.
        
        This method aggregates signals from multiple agents, applies risk management,
        and makes a final trading decision.
        """
        ticker = data["ticker"]
        signals = data["signals"]
        current_price = data.get("current_price")
        
        # Reset daily risk if it's a new day
        self._reset_daily_risk_if_needed()
        
        # Convert dict signals to TradeSignal objects
        trade_signals = []
        for signal in signals:
            if isinstance(signal, dict):
                try:
                    trade_signals.append(TradeSignal(**signal))
                except Exception as e:
                    logger.error(f"Error converting signal to TradeSignal: {str(e)}")
                    continue
            else:
                trade_signals.append(signal)
        
        logger.info(f"Making decision for {ticker} based on {len(trade_signals)} signals")
        
        # If no valid signals, return hold decision
        if not trade_signals:
            return self._create_hold_decision(ticker)
        
        # Analyze signals
        signal_analysis = self._analyze_signals(ticker, trade_signals)
        
        # Check if we have an open position for this ticker
        has_open_position = ticker in self.open_positions
        
        # Make decision based on signal analysis and position status
        if has_open_position:
            decision = self._decide_for_open_position(ticker, signal_analysis, trade_signals)
        else:
            decision = self._decide_for_new_position(ticker, signal_analysis, trade_signals)
        
        # Apply risk management
        decision = self._apply_risk_management(decision)
        
        # Update state based on decision
        self._update_state_from_decision(decision)
        
        # Add to recent decisions
        self._add_to_recent_decisions(decision)
        
        logger.info(f"Decision for {ticker}: {decision.decision} ({decision.confidence:.2f} confidence)")
        
        return decision
    
    def _analyze_signals(self, ticker: str, signals: List[TradeSignal]) -> Dict[str, Any]:
        """Analyze signals to extract key insights."""
        analysis = {
            "long_signals": [],
            "short_signals": [],
            "exit_signals": [],
            "adjust_signals": [],
            "avg_long_confidence": 0.0,
            "avg_short_confidence": 0.0,
            "avg_exit_confidence": 0.0,
            "strongest_long": None,
            "strongest_short": None,
            "strongest_exit": None,
            "timeframes": set(),
            "source_agents": set(),
            "setup_types": set(),
        }
        
        # Categorize signals
        for signal in signals:
            analysis["timeframes"].add(signal.timeframe)
            analysis["source_agents"].add(signal.source_agent)
            analysis["setup_types"].add(signal.setup_type)
            
            if signal.signal_type == "entry":
                if signal.direction == "long":
                    analysis["long_signals"].append(signal)
                    if (analysis["strongest_long"] is None or 
                        signal.confidence > analysis["strongest_long"].confidence):
                        analysis["strongest_long"] = signal
                elif signal.direction == "short":
                    analysis["short_signals"].append(signal)
                    if (analysis["strongest_short"] is None or 
                        signal.confidence > analysis["strongest_short"].confidence):
                        analysis["strongest_short"] = signal
            elif signal.signal_type == "exit":
                analysis["exit_signals"].append(signal)
                if (analysis["strongest_exit"] is None or 
                    signal.confidence > analysis["strongest_exit"].confidence):
                    analysis["strongest_exit"] = signal
            elif signal.signal_type == "adjust":
                analysis["adjust_signals"].append(signal)
        
        # Calculate average confidences
        if analysis["long_signals"]:
            analysis["avg_long_confidence"] = sum(s.confidence for s in analysis["long_signals"]) / len(analysis["long_signals"])
        
        if analysis["short_signals"]:
            analysis["avg_short_confidence"] = sum(s.confidence for s in analysis["short_signals"]) / len(analysis["short_signals"])
        
        if analysis["exit_signals"]:
            analysis["avg_exit_confidence"] = sum(s.confidence for s in analysis["exit_signals"]) / len(analysis["exit_signals"])
        
        # Determine overall bias
        long_weight = len(analysis["long_signals"]) * analysis["avg_long_confidence"]
        short_weight = len(analysis["short_signals"]) * analysis["avg_short_confidence"]
        
        if long_weight > short_weight * 1.5:
            analysis["bias"] = "strongly_bullish"
        elif long_weight > short_weight:
            analysis["bias"] = "bullish"
        elif short_weight > long_weight * 1.5:
            analysis["bias"] = "strongly_bearish"
        elif short_weight > long_weight:
            analysis["bias"] = "bearish"
        else:
            analysis["bias"] = "neutral"
        
        return analysis
    
    def _decide_for_open_position(
        self, ticker: str, signal_analysis: Dict[str, Any], signals: List[TradeSignal]
    ) -> TradeDecision:
        """Make a decision for a ticker with an open position."""
        position = self.open_positions[ticker]
        position_direction = position["direction"]
        
        # Check for exit signals
        if signal_analysis["exit_signals"]:
            # If we have explicit exit signals, consider exiting
            exit_confidence = signal_analysis["avg_exit_confidence"]
            
            if exit_confidence > 0.7:
                # Strong exit signal
                return self._create_exit_decision(
                    ticker, 
                    signals, 
                    exit_confidence,
                    "Strong exit signals detected"
                )
        
        # Check for counter-trend signals
        counter_signals = (signal_analysis["short_signals"] if position_direction == "long" 
                          else signal_analysis["long_signals"])
        
        if counter_signals and signal_analysis["avg_short_confidence" if position_direction == "long" 
                                             else "avg_long_confidence"] > 0.8:
            # Strong counter-trend signal
            return self._create_exit_decision(
                ticker, 
                signals, 
                signal_analysis["avg_short_confidence" if position_direction == "long" 
                               else "avg_long_confidence"],
                "Strong counter-trend signals detected"
            )
        
        # Check for position adjustment
        if signal_analysis["adjust_signals"]:
            # Consider adjusting stop loss or take profit
            return self._create_adjust_decision(ticker, signals)
        
        # Check for reinforcing signals in the same direction
        reinforcing_signals = (signal_analysis["long_signals"] if position_direction == "long" 
                              else signal_analysis["short_signals"])
        
        if reinforcing_signals:
            # Reinforcing signals, hold or potentially add to position
            return self._create_hold_decision(
                ticker,
                "Reinforcing signals support current position"
            )
        
        # Default: hold position
        return self._create_hold_decision(ticker)
    
    def _decide_for_new_position(
        self, ticker: str, signal_analysis: Dict[str, Any], signals: List[TradeSignal]
    ) -> TradeDecision:
        """Make a decision for a ticker without an open position."""
        # Check if we can take new positions
        if len(self.open_positions) >= self.risk_params.max_open_positions:
            return self._create_hold_decision(
                ticker,
                "Maximum number of open positions reached"
            )
        
        # Check for strong directional bias
        if signal_analysis["bias"] in ["strongly_bullish", "strongly_bearish"]:
            direction = "long" if signal_analysis["bias"] == "strongly_bullish" else "short"
            strongest_signal = (signal_analysis["strongest_long"] if direction == "long" 
                               else signal_analysis["strongest_short"])
            
            if strongest_signal and strongest_signal.confidence > 0.7:
                # Strong signal for new position
                return self._create_entry_decision(
                    ticker,
                    direction,
                    signals,
                    strongest_signal.confidence,
                    f"Strong {direction} bias with high confidence signal"
                )
        
        # Check for consensus across multiple timeframes or agents
        if (len(signal_analysis["timeframes"]) > 1 and 
            len(signal_analysis["source_agents"]) > 1):
            
            # If we have signals from multiple timeframes and agents
            if signal_analysis["bias"] in ["bullish", "bearish"]:
                direction = "long" if signal_analysis["bias"] == "bullish" else "short"
                confidence = (signal_analysis["avg_long_confidence"] if direction == "long" 
                             else signal_analysis["avg_short_confidence"])
                
                if confidence > 0.6:
                    # Multi-timeframe, multi-agent consensus
                    return self._create_entry_decision(
                        ticker,
                        direction,
                        signals,
                        confidence,
                        f"Multi-timeframe, multi-agent {direction} consensus"
                    )
        
        # Default: hold (no position)
        return self._create_hold_decision(ticker)
    
    def _apply_risk_management(self, decision: TradeDecision) -> TradeDecision:
        """Apply risk management rules to the decision."""
        # If not an entry decision, no need for risk management
        if decision.decision != "enter":
            return decision
        
        # Check if we have stop loss and take profit
        if decision.stop_loss is None or decision.take_profit is None:
            # Calculate default stop loss and take profit if not provided
            if decision.price is not None:
                direction = decision.direction
                if direction == "long":
                    if decision.stop_loss is None:
                        decision.stop_loss = decision.price * (1 - self.risk_params.default_stop_distance)
                    if decision.take_profit is None:
                        risk = decision.price - decision.stop_loss
                        decision.take_profit = decision.price + (risk * self.risk_params.min_risk_reward)
                elif direction == "short":
                    if decision.stop_loss is None:
                        decision.stop_loss = decision.price * (1 + self.risk_params.default_stop_distance)
                    if decision.take_profit is None:
                        risk = decision.stop_loss - decision.price
                        decision.take_profit = decision.price - (risk * self.risk_params.min_risk_reward)
        
        # Calculate risk-reward ratio
        if decision.stop_loss is not None and decision.take_profit is not None and decision.price is not None:
            if decision.direction == "long":
                risk = decision.price - decision.stop_loss
                reward = decision.take_profit - decision.price
            else:  # short
                risk = decision.stop_loss - decision.price
                reward = decision.price - decision.take_profit
            
            if risk > 0:
                decision.risk_reward = reward / risk
            
            # Check minimum risk-reward ratio
            if decision.risk_reward < self.risk_params.min_risk_reward:
                # Convert to hold if risk-reward is insufficient
                decision.decision = "hold"
                decision.notes.append(f"Insufficient risk-reward ratio: {decision.risk_reward:.2f}")
                return decision
        
        # Calculate position size
        if self.risk_params.position_sizing_method == "fixed_risk" and decision.stop_loss is not None:
            # Calculate position size based on fixed risk percentage
            risk_amount = self.risk_params.account_size * self.risk_params.max_risk_per_trade
            
            if decision.direction == "long":
                risk_per_share = decision.price - decision.stop_loss
            else:  # short
                risk_per_share = decision.stop_loss - decision.price
            
            if risk_per_share > 0:
                decision.position_size = risk_amount / risk_per_share
        elif self.risk_params.position_sizing_method == "fixed_size":
            # Use a fixed position size
            decision.position_size = self.risk_params.account_size * 0.1  # 10% of account
        
        # Check daily risk limit
        if decision.position_size is not None and decision.stop_loss is not None:
            potential_loss = 0
            if decision.direction == "long":
                potential_loss = (decision.price - decision.stop_loss) * decision.position_size
            else:  # short
                potential_loss = (decision.stop_loss - decision.price) * decision.position_size
            
            # Check if this trade would exceed daily risk limit
            if (self.daily_risk_used + potential_loss) > (self.risk_params.account_size * self.risk_params.max_risk_per_day):
                # Convert to hold if daily risk would be exceeded
                decision.decision = "hold"
                decision.notes.append("Daily risk limit would be exceeded")
                return decision
        
        # Check correlation with existing positions
        ticker_sector = self._get_ticker_sector(decision.ticker)
        correlated_positions = 0
        
        for pos_ticker in self.open_positions:
            if self._get_ticker_sector(pos_ticker) == ticker_sector:
                correlated_positions += 1
        
        if correlated_positions >= self.risk_params.max_correlated_positions:
            # Convert to hold if too many correlated positions
            decision.decision = "hold"
            decision.notes.append(f"Too many correlated positions in {ticker_sector} sector")
            return decision
        
        return decision
    
    def _update_state_from_decision(self, decision: TradeDecision) -> None:
        """Update agent state based on the decision."""
        ticker = decision.ticker
        
        if decision.decision == "enter":
            # Add new position
            self.open_positions[ticker] = {
                "direction": decision.direction,
                "entry_price": decision.price,
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
                "position_size": decision.position_size,
                "entry_time": datetime.now(),
                "timeframe": decision.timeframe
            }
            
            # Update daily risk used
            if decision.position_size is not None and decision.stop_loss is not None:
                if decision.direction == "long":
                    risk = (decision.price - decision.stop_loss) * decision.position_size
                else:  # short
                    risk = (decision.stop_loss - decision.price) * decision.position_size
                
                self.daily_risk_used += risk
        
        elif decision.decision == "exit":
            # Remove position
            if ticker in self.open_positions:
                del self.open_positions[ticker]
        
        elif decision.decision == "adjust":
            # Update position parameters
            if ticker in self.open_positions:
                if decision.stop_loss is not None:
                    self.open_positions[ticker]["stop_loss"] = decision.stop_loss
                
                if decision.take_profit is not None:
                    self.open_positions[ticker]["take_profit"] = decision.take_profit
    
    def _reset_daily_risk_if_needed(self) -> None:
        """Reset daily risk if it's a new day."""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.daily_risk_used = 0.0
            self.last_reset_date = current_date
            logger.info("Daily risk reset")
    
    def _add_to_recent_decisions(self, decision: TradeDecision) -> None:
        """Add decision to recent decisions history."""
        self.recent_decisions.append(decision)
        
        # Limit the size of recent decisions
        if len(self.recent_decisions) > self.max_recent_decisions:
            self.recent_decisions = self.recent_decisions[-self.max_recent_decisions:]
    
    def _create_entry_decision(
        self, ticker: str, direction: str, signals: List[TradeSignal], 
        confidence: float, reasoning: str
    ) -> TradeDecision:
        """Create an entry decision."""
        # Find the strongest signal for this direction
        strongest_signal = None
        for signal in signals:
            if (signal.signal_type == "entry" and signal.direction == direction and
                (strongest_signal is None or signal.confidence > strongest_signal.confidence)):
                strongest_signal = signal
        
        # Use the strongest signal for price, stop loss, and take profit if available
        price = strongest_signal.price if strongest_signal else None
        stop_loss = strongest_signal.stop_loss if strongest_signal else None
        take_profit = strongest_signal.take_profit if strongest_signal else None
        timeframe = strongest_signal.timeframe if strongest_signal else ""
        
        notes = [reasoning]
        if strongest_signal and strongest_signal.notes:
            notes.append(strongest_signal.notes)
        
        return TradeDecision(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            decision="enter",
            direction=direction,
            price=price,
            confidence=confidence,
            signals=signals,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timeframe=timeframe,
            notes=notes,
            reasoning=reasoning
        )
    
    def _create_exit_decision(
        self, ticker: str, signals: List[TradeSignal], 
        confidence: float, reasoning: str
    ) -> TradeDecision:
        """Create an exit decision."""
        # Get current position details
        position = self.open_positions.get(ticker, {})
        direction = position.get("direction")
        
        notes = [reasoning]
        
        # Find the strongest exit signal
        strongest_signal = None
        for signal in signals:
            if (signal.signal_type == "exit" and
                (strongest_signal is None or signal.confidence > strongest_signal.confidence)):
                strongest_signal = signal
        
        if strongest_signal and strongest_signal.notes:
            notes.append(strongest_signal.notes)
        
        return TradeDecision(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            decision="exit",
            direction=direction,
            price=strongest_signal.price if strongest_signal else None,
            confidence=confidence,
            signals=signals,
            notes=notes,
            reasoning=reasoning
        )
    
    def _create_hold_decision(self, ticker: str, reasoning: str = "Insufficient signals for action") -> TradeDecision:
        """Create a hold decision."""
        return TradeDecision(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            decision="hold",
            confidence=1.0,  # High confidence in holding
            notes=[reasoning],
            reasoning=reasoning
        )
    
    def _create_adjust_decision(self, ticker: str, signals: List[TradeSignal]) -> TradeDecision:
        """Create a position adjustment decision."""
        # Get current position details
        position = self.open_positions.get(ticker, {})
        direction = position.get("direction")
        
        # Find the strongest adjustment signal
        strongest_signal = None
        for signal in signals:
            if (signal.signal_type == "adjust" and
                (strongest_signal is None or signal.confidence > strongest_signal.confidence)):
                strongest_signal = signal
        
        if not strongest_signal:
            return self._create_hold_decision(ticker)
        
        notes = [f"Adjusting position based on {strongest_signal.source_agent} signal"]
        if strongest_signal.notes:
            notes.append(strongest_signal.notes)
        
        return TradeDecision(
            ticker=ticker,
            timestamp=datetime.now().isoformat(),
            decision="adjust",
            direction=direction,
            price=strongest_signal.price,
            confidence=strongest_signal.confidence,
            signals=signals,
            stop_loss=strongest_signal.stop_loss,
            take_profit=strongest_signal.take_profit,
            notes=notes,
            reasoning=f"Position adjustment from {strongest_signal.source_agent}"
        )
    
    def _get_ticker_sector(self, ticker: str) -> str:
        """Get the sector for a ticker (placeholder implementation)."""
        # In a real implementation, this would look up the sector from a database
        # For now, we'll use a simple mapping for demonstration
        tech_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"]
        finance_tickers = ["JPM", "BAC", "WFC", "GS", "MS", "V", "MA"]
        energy_tickers = ["XOM", "CVX", "COP", "EOG", "SLB"]
        
        if ticker in tech_tickers:
            return "Technology"
        elif ticker in finance_tickers:
            return "Finance"
        elif ticker in energy_tickers:
            return "Energy"
        else:
            return "Unknown"
    
    def get_open_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get all open positions."""
        return self.open_positions
    
    def get_position(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get position details for a specific ticker."""
        return self.open_positions.get(ticker)
    
    def get_recent_decisions(self, limit: int = 10) -> List[TradeDecision]:
        """Get recent trading decisions."""
        return self.recent_decisions[-limit:] if self.recent_decisions else []
    
    def update_risk_parameters(self, risk_params: Dict[str, Any]) -> None:
        """Update risk management parameters."""
        for key, value in risk_params.items():
            if hasattr(self.risk_params, key):
                setattr(self.risk_params, key, value)
        
        logger.info("Risk parameters updated")
    
    def get_risk_parameters(self) -> RiskParameters:
        """Get current risk management parameters."""
        return self.risk_params
    
    def get_daily_risk_used(self) -> float:
        """Get the amount of daily risk used."""
        return self.daily_risk_used 