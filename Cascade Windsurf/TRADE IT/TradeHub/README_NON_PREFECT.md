# Non-Prefect Trading System

This directory contains a simplified version of the trading system that does not depend on Prefect. This makes it more reliable when Prefect versions change or when there are compatibility issues with Prefect.

## Overview

The non-Prefect trading system includes the following components:

1. **Setup Scanner** - Scans for trading setups like breaker blocks and fair value gaps
2. **Market Analysis** - Analyzes market conditions and evaluates existing setups
3. **Unified Runner** - A script that can run both workflows in sequence

## Files

- `non_prefect_setup_scanner.py` - Setup scanner workflow without Prefect
- `non_prefect_market_analysis.py` - Market analysis workflow without Prefect
- `run_trading_workflows.py` - Unified runner for both workflows

## Usage

### Running the Unified Workflow

The unified workflow runner can run either the setup scanner, the market analysis, or both in sequence:

```bash
# Run both workflows
python run_trading_workflows.py --workflow both --symbols AAPL MSFT --timeframes 1D

# Run only the setup scanner
python run_trading_workflows.py --workflow scanner --symbols AAPL MSFT --timeframes 1D

# Run only the market analysis
python run_trading_workflows.py --workflow analysis --symbols AAPL MSFT --timeframes 1D
```

### Running Individual Workflows

You can also run each workflow individually:

```bash
# Run the setup scanner
python non_prefect_setup_scanner.py --symbols AAPL MSFT --timeframes 1D

# Run the market analysis
python non_prefect_market_analysis.py --symbols AAPL MSFT --timeframes 1D
```

## Features

### Setup Scanner

The setup scanner workflow:

- Fetches market data for specified symbols and timeframes
- Scans for breaker blocks and fair value gaps
- Identifies potential trading setups
- Stores the setups for later analysis

### Market Analysis

The market analysis workflow:

- Fetches market data for specified symbols and timeframes
- Analyzes market conditions using technical indicators
- Evaluates existing setups for confluence with market conditions
- Updates setup status based on confluence score

## Dependencies

The non-Prefect trading system depends on the following Python packages:

- `pandas` - For data manipulation
- `yfinance` - For fetching market data
- `loguru` - For logging

## Logs

All workflows generate detailed logs in the `logs` directory. The logs include:

- Workflow start and end times
- Data fetching results
- Analysis results
- Setup identification and evaluation
- Errors and warnings

## Extending the System

To extend the system, you can:

1. Implement real breaker block and fair value gap scanners in `non_prefect_setup_scanner.py`
2. Add more technical indicators to the market analyzer in `non_prefect_market_analysis.py`
3. Implement a database backend for storing setups and analysis results
4. Add a web interface for viewing setups and analysis results

## Comparison with Prefect Version

The non-Prefect version:

- Is more reliable when Prefect versions change
- Has fewer dependencies
- Is easier to understand and modify
- Has the same core functionality as the Prefect version
- Lacks the advanced features of Prefect like scheduling, retries, and monitoring

## License

This project is licensed under the MIT License - see the LICENSE file for details. 