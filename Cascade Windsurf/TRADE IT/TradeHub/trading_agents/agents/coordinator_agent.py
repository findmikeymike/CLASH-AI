"""
Coordinator Agent - The central orchestrator for the multi-agent trading system.
This agent manages the flow of data between different specialized agents and
coordinates the overall trading pipeline.
"""

from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from .base_agent import BaseAgent, AgentState
from .order_flow_agent import OrderFlowAgent
from .options_agent import OptionsExpertAgent
from .breaker_block_agent import BreakerBlockAgent
from .fvg_agent import FVGAgent
from .decision_agent import DecisionAgent
from .market_analyzer_agent import MarketAnalyzerAgent
from .enhanced_options_agent import EnhancedOptionsExpertAgent

class SetupType(BaseModel):
    """Model for a trading setup type."""
    name: str
    description: str
    required_agents: List[str]
    parameters: Dict[str, Any] = {}

class TradeSetup(BaseModel):
    """Model for a detected trade setup."""
    setup_type: str
    ticker: str
    timeframe: str
    timestamp: str
    entry_price: float
    stop_loss: float
    take_profit: float
    direction: int  # 1 for long, -1 for short
    confidence: float  # 0.0 to 1.0
    analysis: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent that orchestrates the flow of data between different specialized agents.
    This agent manages the overall trading pipeline and coordinates the execution of different
    agents based on the detected setups.
    """
    
    def __init__(self, agent_id: str = "coordinator_agent", config: Optional[Dict[str, Any]] = None):
        """Initialize the Coordinator Agent."""
        super().__init__(agent_id, config or {})
        self.setup_types = self._initialize_setup_types()
        self.agents = {}
        self._initialize_agents()
        
    def _initialize_setup_types(self) -> Dict[str, SetupType]:
        """Initialize the available setup types."""
        return {
            "breaker_block": SetupType(
                name="Breaker Block Retest",
                description="Price retesting a breaker block level",
                required_agents=["scanner_agent", "market_analyzer", "order_flow_agent"],
                parameters={
                    "lookback_periods": 50,
                    "min_volume_threshold": 10000,
                    "price_rejection_threshold": 0.005,
                }
            ),
            "fair_value_gap": SetupType(
                name="Fair Value Gap",
                description="Price filling a fair value gap",
                required_agents=["scanner_agent", "market_analyzer"],
                parameters={
                    "fvg_threshold": 0.003,
                }
            ),
            "options_flow": SetupType(
                name="Options Flow Signal",
                description="Unusual options activity indicating directional bias",
                required_agents=["options_agent", "market_analyzer"],
                parameters={
                    "volume_threshold": 3.0,  # Multiple of average volume
                    "open_interest_ratio": 1.5,
                }
            ),
            # Add more setup types as needed
        }
    
    def _initialize_agents(self):
        """Initialize the required agents."""
        # Create instances of all required agents
        self.agents["market_analyzer"] = MarketAnalyzerAgent(config={
            'market_tickers': ['^GSPC', 'QQQ', 'IWM', 'SPY'],
            'sector_tickers': ['XLK', 'XLF', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLB', 'XLRE'],
            'options_tickers': ['SPY', 'QQQ'],
            'cache_ttl': 60  # minutes
        })
        self.agents["breaker_block_agent"] = BreakerBlockAgent()
        self.agents["fvg_agent"] = FVGAgent()
        self.agents["order_flow_agent"] = OrderFlowAgent()
        
        # Use the enhanced options agent instead of the regular one
        self.agents["options_agent"] = EnhancedOptionsExpertAgent(config={
            "volume_threshold": 3.0,
            "open_interest_ratio": 1.5,
            "stop_hunt_sensitivity": 0.7
        })
        
        self.agents["decision_agent"] = DecisionAgent()
        
        logger.info(f"Initialized {len(self.agents)} specialized agents")
    
    async def validate(self, data: Any) -> bool:
        """Validate input data."""
        if not isinstance(data, dict):
            logger.error("Input data must be a dictionary")
            return False
        
        required_fields = ["tickers", "timeframes"]
        if not all(field in data for field in required_fields):
            logger.error(f"Missing required fields: {required_fields}")
            return False
        
        return True
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data through the multi-agent pipeline.
        
        Args:
            data: Dictionary containing tickers, timeframes, and OHLC data
            
        Returns:
            Dictionary with results from the multi-agent analysis
        """
        logger.info(f"Processing {len(data.get('tickers', []))} tickers across {len(data.get('timeframes', []))} timeframes")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "setups": [],
            "confluences": [],
            "trade_recommendations": []
        }
        
        # First, run market analyzer to get overall market context
        market_analysis_result = await self.agents["market_analyzer"].run(data)
        
        if market_analysis_result["success"]:
            # Add market analysis to results
            results["market_analysis"] = market_analysis_result["result"].get("market_analysis", {})
            results["sector_analysis"] = market_analysis_result["result"].get("sector_analysis", {})
            
            # Update data with market context for other agents
            data["market_analysis"] = results["market_analysis"]
            data["sector_analysis"] = results["sector_analysis"]
            
            logger.info(f"Market analysis completed with stance: {results['market_analysis'].get('market_stance', 'unknown')}")
        else:
            logger.warning("Market analysis failed, continuing without market context")
        
        # Process each ticker and timeframe
        for ticker in data.get("tickers", []):
            ohlc_data = data.get("ohlc_data", {}).get(ticker, {})
            setups = []
            
            for timeframe in data.get("timeframes", []):
                if timeframe in ohlc_data:
                    # Run breaker block agent
                    breaker_data = {
                        "ticker": ticker,
                        "timeframe": timeframe,
                        "ohlc_data": ohlc_data[timeframe]
                    }
                    
                    breaker_result = await self.agents["breaker_block_agent"].run(breaker_data)
                    
                    if breaker_result["success"]:
                        # Process breaker blocks
                        breaker_setups = self._process_breaker_blocks(
                            ticker, timeframe, breaker_result["result"]
                        )
                        setups.extend(breaker_setups)
                    
                    # Run FVG agent
                    fvg_data = {
                        "ticker": ticker,
                        "timeframe": timeframe,
                        "ohlc_data": ohlc_data[timeframe]
                    }
                    
                    fvg_result = await self.agents["fvg_agent"].run(fvg_data)
                    
                    if fvg_result["success"]:
                        # Process fair value gaps
                        fvg_setups = self._process_fair_value_gaps(
                            ticker, timeframe, fvg_result["result"]
                        )
                        setups.extend(fvg_setups)
            
            # Run options agent for additional analysis
            options_data = {
                "ticker": ticker
            }
            
            options_result = await self.agents["options_agent"].run(options_data)
            
            if options_result["success"]:
                # Process options analysis
                options_setups = self._process_options_analysis(
                    ticker, options_result["result"]
                )
                setups.extend(options_setups)
            
            # Detect confluences between setups
            confluences = self._detect_confluences(setups)
            
            # Generate final recommendations
            recommendations = self._generate_recommendations(setups, confluences)
            
            # Add results to overall results
            results["setups"].extend(setups)
            results["confluences"].extend(confluences)
            results["trade_recommendations"].extend(recommendations)
        
        logger.info(f"Multi-agent pipeline completed: found {len(results['setups'])} setups and {len(results['confluences'])} confluences")
        
        return results
    
    def _process_breaker_blocks(
        self, ticker: str, timeframe: str, breaker_result: Any
    ) -> List[TradeSetup]:
        """Process breaker block scan results into trade setups."""
        setups = []
        
        # Extract active retests from the breaker block scan
        active_retests = breaker_result.active_retests
        
        for retest in active_retests:
            # Calculate entry, stop loss, and take profit
            mid_price = (retest.high + retest.low) / 2
            
            if retest.direction == "bullish":
                entry_price = mid_price
                stop_loss = retest.low * 0.99  # Just below the breaker block
                take_profit = entry_price + (entry_price - stop_loss) * 3  # 3:1 risk-reward
                direction = 1  # Long
            else:  # bearish
                entry_price = mid_price
                stop_loss = retest.high * 1.01  # Just above the breaker block
                take_profit = entry_price - (stop_loss - entry_price) * 3  # 3:1 risk-reward
                direction = -1  # Short
            
            # Calculate confidence based on strength and confluence count
            confidence = min(1.0, retest.strength * (1 + retest.confluence_count * 0.2))
            
            # Create trade setup
            setup = TradeSetup(
                setup_type="Breaker Block Retest",
                ticker=ticker,
                timeframe=timeframe,
                timestamp=datetime.now().isoformat(),
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                direction=direction,
                confidence=confidence,
                analysis={
                    "breaker_direction": retest.direction,
                    "breaker_strength": retest.strength,
                    "confluence_count": retest.confluence_count,
                    "notes": retest.notes
                }
            )
            
            setups.append(setup)
        
        return setups
    
    def _process_fair_value_gaps(
        self, ticker: str, timeframe: str, fvg_result: Any
    ) -> List[TradeSetup]:
        """Process fair value gap scan results into trade setups."""
        setups = []
        
        # Extract active FVGs from the scan
        active_fvgs = fvg_result.active_fvgs
        
        for fvg in active_fvgs:
            # Calculate entry, stop loss, and take profit
            mid_price = (fvg.high + fvg.low) / 2
            
            if fvg.direction == "bullish":
                entry_price = mid_price
                stop_loss = fvg.low * 0.99  # Just below the FVG
                take_profit = entry_price + (entry_price - stop_loss) * 2.5  # 2.5:1 risk-reward
                direction = 1  # Long
            else:  # bearish
                entry_price = mid_price
                stop_loss = fvg.high * 1.01  # Just above the FVG
                take_profit = entry_price - (stop_loss - entry_price) * 2.5  # 2.5:1 risk-reward
                direction = -1  # Short
            
            # Calculate confidence based on strength and confluence count
            confidence = min(1.0, fvg.strength * (1 + fvg.confluence_count * 0.2))
            
            # Create trade setup
            setup = TradeSetup(
                setup_type="Fair Value Gap",
                ticker=ticker,
                timeframe=timeframe,
                timestamp=datetime.now().isoformat(),
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                direction=direction,
                confidence=confidence,
                analysis={
                    "fvg_direction": fvg.direction,
                    "fvg_strength": fvg.strength,
                    "confluence_count": fvg.confluence_count,
                    "age_in_bars": fvg.age_in_bars,
                    "notes": fvg.notes
                }
            )
            
            setups.append(setup)
        
        return setups
    
    def _process_options_analysis(
        self, ticker: str, options_result: Any
    ) -> List[TradeSetup]:
        """Process options analysis results into trade setups."""
        setups = []
        
        # Check if we're using the enhanced options agent
        if hasattr(options_result, 'options_sentiment') and hasattr(options_result, 'confidence_level'):
            # Enhanced options agent output format
            sentiment = options_result.options_sentiment
            confidence_level = options_result.confidence_level
            
            # Map confidence level to numeric value
            confidence_map = {
                'high': 0.9,
                'medium': 0.7,
                'low': 0.5
            }
            confidence_value = confidence_map.get(confidence_level, 0.7)
            
            # Only create a setup if there's a strong directional bias
            if sentiment in ["strongly_bullish", "bullish", "strongly_bearish", "bearish"]:
                # Get current price (approximate from recommended contracts if available)
                current_price = 100.0  # Default placeholder
                if hasattr(options_result, 'recommended_contracts') and options_result.recommended_contracts:
                    # Use the first recommended contract's strike as an approximation
                    current_price = options_result.recommended_contracts[0].get('strike', 100.0)
                
                # Set direction
                direction = 1 if sentiment in ["strongly_bullish", "bullish"] else -1
                
                # Calculate entry, stop loss, and take profit
                entry_price = current_price
                
                # Adjust risk based on sentiment strength
                risk_pct = 0.02 if sentiment in ["strongly_bullish", "strongly_bearish"] else 0.03
                reward_pct = risk_pct * 2.5  # 2.5:1 risk-reward
                
                if direction == 1:  # bullish
                    stop_loss = current_price * (1 - risk_pct)
                    take_profit = current_price * (1 + reward_pct)
                else:  # bearish
                    stop_loss = current_price * (1 + risk_pct)
                    take_profit = current_price * (1 - reward_pct)
                
                # Create trade setup
                setup = TradeSetup(
                    setup_type="Enhanced Options Signal",
                    ticker=ticker,
                    timeframe="daily",  # Options typically affect daily timeframe
                    timestamp=datetime.now().isoformat(),
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    direction=direction,
                    confidence=confidence_value,
                    analysis={
                        "options_sentiment": sentiment,
                        "confidence_level": confidence_level,
                        "unusual_activity": options_result.unusual_activity if hasattr(options_result, 'unusual_activity') else {},
                        "sweep_activity": options_result.sweep_activity if hasattr(options_result, 'sweep_activity') else {},
                        "gex_analysis": options_result.gex_analysis if hasattr(options_result, 'gex_analysis') else {},
                        "risk_warnings": options_result.risk_warnings if hasattr(options_result, 'risk_warnings') else []
                    }
                )
                
                # Add stop hunt warnings if present
                if hasattr(options_result, 'bullish_stop_hunt_warning'):
                    setup.analysis["bullish_stop_hunt_warning"] = options_result.bullish_stop_hunt_warning
                
                if hasattr(options_result, 'bearish_stop_hunt_warning'):
                    setup.analysis["bearish_stop_hunt_warning"] = options_result.bearish_stop_hunt_warning
                
                setups.append(setup)
                
        else:
            # Original options agent output format
            analysis = options_result.analysis
            
            # Only create a setup if there's a strong directional bias
            if "overall_bias" in analysis and analysis["overall_bias"]["strength"] > 0.7:
                direction_str = analysis["overall_bias"]["direction"]
                
                if direction_str in ["bullish", "bearish"]:
                    # Get current price (approximate from signals if available)
                    current_price = 100.0  # Default placeholder
                    if options_result.signals:
                        current_price = options_result.signals[0].strike
                    
                    # Set direction
                    direction = 1 if direction_str == "bullish" else -1
                    
                    # Calculate entry, stop loss, and take profit
                    entry_price = current_price
                    
                    if direction == 1:  # bullish
                        stop_loss = current_price * 0.97  # 3% below
                        take_profit = current_price * 1.06  # 6% above (2:1 risk-reward)
                    else:  # bearish
                        stop_loss = current_price * 1.03  # 3% above
                        take_profit = current_price * 0.94  # 6% below (2:1 risk-reward)
                    
                    # Calculate confidence based on strength and signal count
                    signal_count = len(options_result.signals)
                    confidence = min(1.0, analysis["overall_bias"]["strength"] * (1 + signal_count * 0.1))
                    
                    # Create trade setup
                    setup = TradeSetup(
                        setup_type="Options Flow Signal",
                        ticker=ticker,
                        timeframe="daily",  # Options typically affect daily timeframe
                        timestamp=datetime.now().isoformat(),
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        direction=direction,
                        confidence=confidence,
                        analysis={
                            "options_direction": direction_str,
                            "options_strength": analysis["overall_bias"]["strength"],
                            "call_put_ratio": options_result.call_put_ratio,
                            "iv_percentile": options_result.iv_percentile,
                            "signal_count": signal_count,
                            "notes": analysis["notes"] if "notes" in analysis else ""
                        }
                    )
                    
                    setups.append(setup)
        
        return setups
    
    def _detect_confluences(self, setups: List[TradeSetup]) -> List[Dict[str, Any]]:
        """
        Detect confluences between different setups.
        
        Confluences occur when multiple setups point to similar price levels or
        directions across different timeframes or setup types.
        """
        if not setups:
            return []
        
        # Group setups by ticker
        ticker_setups = {}
        for setup in setups:
            if setup.ticker not in ticker_setups:
                ticker_setups[setup.ticker] = []
            ticker_setups[setup.ticker].append(setup)
        
        confluences = []
        
        # For each ticker, find confluences
        for ticker, ticker_setups_list in ticker_setups.items():
            # Group by direction (bullish/bearish)
            bullish_setups = [s for s in ticker_setups_list if s.direction > 0]
            bearish_setups = [s for s in ticker_setups_list if s.direction < 0]
            
            # Process bullish confluences
            bullish_confluences = self._find_price_level_confluences(bullish_setups)
            for conf in bullish_confluences:
                confluences.append({
                    "ticker": ticker,
                    "direction": "bullish",
                    "setups": conf["setups"],
                    "price_level": conf["price_level"],
                    "strength": conf["strength"],
                    "timeframes": conf["timeframes"],
                    "setup_types": conf["setup_types"]
                })
            
            # Process bearish confluences
            bearish_confluences = self._find_price_level_confluences(bearish_setups)
            for conf in bearish_confluences:
                confluences.append({
                    "ticker": ticker,
                    "direction": "bearish",
                    "setups": conf["setups"],
                    "price_level": conf["price_level"],
                    "strength": conf["strength"],
                    "timeframes": conf["timeframes"],
                    "setup_types": conf["setup_types"]
                })
        
        return confluences
    
    def _find_price_level_confluences(self, setups: List[TradeSetup]) -> List[Dict[str, Any]]:
        """Find confluences at similar price levels."""
        if len(setups) < 2:
            return []
        
        # Sort setups by entry price
        sorted_setups = sorted(setups, key=lambda s: s.entry_price)
        
        # Group setups by similar price levels
        # Two setups are considered at the same level if they are within 1% of each other
        price_groups = []
        current_group = [sorted_setups[0]]
        
        for i in range(1, len(sorted_setups)):
            current_setup = sorted_setups[i]
            prev_setup = sorted_setups[i-1]
            
            # Check if current setup is within 1% of previous setup
            price_diff_pct = abs(current_setup.entry_price - prev_setup.entry_price) / prev_setup.entry_price
            
            if price_diff_pct <= 0.01:  # 1% threshold
                current_group.append(current_setup)
            else:
                # Start a new group if price difference is too large
                if len(current_group) >= 2:
                    price_groups.append(current_group)
                current_group = [current_setup]
        
        # Add the last group if it has at least 2 setups
        if len(current_group) >= 2:
            price_groups.append(current_group)
        
        # Convert groups to confluence objects
        confluences = []
        
        for group in price_groups:
            # Calculate average price level
            avg_price = sum(s.entry_price for s in group) / len(group)
            
            # Calculate confluence strength based on:
            # 1. Number of setups in the confluence
            # 2. Diversity of timeframes
            # 3. Diversity of setup types
            # 4. Average confidence of setups
            
            timeframes = set(s.timeframe for s in group)
            setup_types = set(s.setup_type for s in group)
            avg_confidence = sum(s.confidence for s in group) / len(group)
            
            # More setups, timeframes, and setup types increase strength
            base_strength = min(0.5, 0.1 * len(group))
            timeframe_bonus = min(0.2, 0.05 * len(timeframes))
            setup_type_bonus = min(0.2, 0.1 * len(setup_types))
            confidence_factor = avg_confidence
            
            strength = min(1.0, base_strength + timeframe_bonus + setup_type_bonus + confidence_factor)
            
            confluences.append({
                "setups": group,
                "price_level": avg_price,
                "strength": strength,
                "timeframes": list(timeframes),
                "setup_types": list(setup_types)
            })
        
        return confluences
    
    def _generate_recommendations(
        self, setups: List[TradeSetup], confluences: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate final trade recommendations based on setups and confluences.
        
        This method prioritizes confluences and high-confidence setups to produce
        actionable trade recommendations.
        """
        recommendations = []
        
        # First, process confluences (higher priority)
        for conf in confluences:
            # Calculate risk-reward ratio
            best_setup = max(conf["setups"], key=lambda s: s.confidence)
            
            risk = abs(best_setup.entry_price - best_setup.stop_loss)
            reward = abs(best_setup.take_profit - best_setup.entry_price)
            risk_reward = reward / risk if risk > 0 else 0
            
            # Only recommend trades with good risk-reward
            if risk_reward >= 2.0 and conf["strength"] >= 0.6:
                recommendation = {
                    "ticker": conf["ticker"],
                    "direction": conf["direction"],
                    "entry_price": conf["price_level"],
                    "stop_loss": best_setup.stop_loss,
                    "take_profit": best_setup.take_profit,
                    "confidence": conf["strength"],
                    "risk_reward_ratio": risk_reward,
                    "timeframes": conf["timeframes"],
                    "setup_types": conf["setup_types"],
                    "source": "confluence",
                    "notes": f"Strong confluence of {len(conf['setups'])} setups across {len(conf['timeframes'])} timeframes"
                }
                recommendations.append(recommendation)
        
        # Then, process high-confidence individual setups that aren't part of confluences
        confluence_setups = set()
        for conf in confluences:
            for setup in conf["setups"]:
                confluence_setups.add(id(setup))
        
        for setup in setups:
            # Skip setups that are already part of confluences
            if id(setup) in confluence_setups:
                continue
            
            # Only recommend high-confidence individual setups
            if setup.confidence >= 0.75:
                risk = abs(setup.entry_price - setup.stop_loss)
                reward = abs(setup.take_profit - setup.entry_price)
                risk_reward = reward / risk if risk > 0 else 0
                
                if risk_reward >= 2.5:  # Higher threshold for individual setups
                    direction_str = "bullish" if setup.direction > 0 else "bearish"
                    recommendation = {
                        "ticker": setup.ticker,
                        "direction": direction_str,
                        "entry_price": setup.entry_price,
                        "stop_loss": setup.stop_loss,
                        "take_profit": setup.take_profit,
                        "confidence": setup.confidence,
                        "risk_reward_ratio": risk_reward,
                        "timeframes": [setup.timeframe],
                        "setup_types": [setup.setup_type],
                        "source": "individual",
                        "notes": f"High-confidence {setup.setup_type} setup on {setup.timeframe} timeframe"
                    }
                    recommendations.append(recommendation)
        
        # Sort recommendations by confidence (descending)
        recommendations.sort(key=lambda r: r["confidence"], reverse=True)
        
        return recommendations 