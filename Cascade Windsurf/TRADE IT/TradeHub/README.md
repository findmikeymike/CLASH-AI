# Trading Agent System

A modular trading system that utilizes multiple specialized agents working together in a DAG workflow using Prefect.

## Project Structure

```
trading_agents/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── market_analyzer.py
│   ├── technical_analyzer.py
│   ├── risk_manager.py
│   └── execution_agent.py
├── workflows/
│   ├── __init__.py
│   └── trading_dag.py
├── utils/
│   ├── __init__.py
│   └── logging_config.py
├── custom_dashboard/    # Flask-based dashboard with TradingView charts
│   ├── __init__.py
│   ├── api.py
│   ├── views.py
│   ├── tradingview.py
│   ├── templates/
│   └── static/
└── config/
    └── settings.py
```

## Features

- Modular agent-based architecture
- Prefect DAG workflow orchestration
- Specialized agents for different trading tasks:
  - Market Analysis
  - Technical Analysis
  - Risk Management
  - Trade Execution
- Modern dashboard with TradingView Lightweight Charts integration
- Real-time order flow analysis
- Comprehensive logging system
- Configuration management

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

Run the trading workflow:
```bash
python -m workflows.trading_dag
```

Run the TradingView dashboard:
```bash
python run_tradingview_dashboard.py
```

## Dashboard

The system includes a modern trading dashboard built with Flask and TradingView Lightweight Charts, featuring:

- Real-time price charts with multiple timeframes
- Order flow analysis
- Trade setup visualization
- Market analysis tools
- Watchlists
- Backtesting interface

## Logging

Logs are stored in the `logs` directory with different levels of detail for debugging and monitoring. 