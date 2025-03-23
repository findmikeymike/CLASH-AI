# Trade Hub - Continuous Setup Scanner

This document provides instructions on how to use the continuous setup scanner with Interactive Brokers (IBKR) or Yahoo Finance data.

## Overview

The continuous setup scanner is designed to run at regular intervals, scanning for various trading setups such as:

- Breaker blocks
- Fair value gaps
- Sweep Engulfer patterns
- Sweeping Engulfer patterns

The scanner can use either Interactive Brokers (IBKR) or Yahoo Finance as a data source, with IBKR being the preferred option for real-time data during market hours.

## Prerequisites

### For Yahoo Finance Data (Default)

- Python 3.7 or higher
- Required packages: `pandas`, `numpy`, `yfinance`, `loguru`, `schedule`, `pytz`

### For Interactive Brokers Data

- All of the above
- Interactive Brokers Trader Workstation (TWS) or IB Gateway installed and running
- API access enabled in TWS/IB Gateway
- `ib_insync` package installed

## Setup

1. Install the required packages:

```bash
pip install pandas numpy yfinance loguru schedule pytz ib_insync
```

2. If using IBKR, make sure TWS or IB Gateway is running with API access enabled:
   - In TWS: File > Global Configuration > API > Settings
   - Check "Enable ActiveX and Socket Clients"
   - Set the port (default is 7497 for paper trading, 7496 for live trading)
   - Uncheck "Read-Only API"

## Usage

### Standard Continuous Scanner (Yahoo Finance)

```bash
python continuous_scanner.py --symbols AAPL MSFT GOOGL --timeframes 1D --interval 5
```

### IBKR Continuous Scanner

```bash
python ibkr_continuous_scanner.py --symbols AAPL MSFT GOOGL --timeframes 1D --interval 5
```

### Command Line Arguments

- `--symbols`: List of symbols to scan (default: AAPL, MSFT, GOOGL, AMZN, TSLA, NVDA, META)
- `--timeframes`: List of timeframes to scan (default: 1D)
- `--interval`: How often to run the scanner in minutes (default: 5)
- `--lookback`: Number of periods to look back for pattern recognition (default: 50)
- `--min-volume`: Minimum volume to consider a candle significant (default: 10000)
- `--price-rejection`: Threshold for price rejection (default: 0.005)
- `--fvg-threshold`: Threshold for fair value gaps (default: 0.003)
- `--min-touches`: Minimum touches to consider a level significant (default: 2)
- `--retest-threshold`: Threshold for retest (default: 0.005)
- `--retracement-threshold`: Threshold for retracement in sweeping engulfer patterns (default: 0.33)
- `--period`: Period to fetch data for (default: 1y)
- `--scan-outside-market-hours`: Run scans even when the market is closed

## IBKR Configuration

The IBKR connector is configured with the following default settings:

- Host: 127.0.0.1 (localhost)
- Port: 7497 (paper trading) or 7496 (live trading)
- Client ID: 1

If you need to change these settings, edit the `trading_agents/utils/ibkr_connector.py` file.

## Viewing Setups

The scanner stores all detected setups in the `data/setups` directory as JSON files. You can view a summary of all setups by running:

```bash
python summarize_setups.py
```

This will generate a summary of all unique setups found across all symbols and timeframes.

## Running as a Service

To run the scanner as a background service that starts automatically, you can use tools like:

- On Linux: systemd
- On macOS: launchd
- On Windows: Task Scheduler

Example systemd service file (`/etc/systemd/system/trade-hub-scanner.service`):

```
[Unit]
Description=Trade Hub Continuous Scanner
After=network.target

[Service]
User=yourusername
WorkingDirectory=/path/to/trade-hub
ExecStart=/usr/bin/python3 /path/to/trade-hub/ibkr_continuous_scanner.py --symbols AAPL MSFT GOOGL --timeframes 1D --interval 5
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable trade-hub-scanner
sudo systemctl start trade-hub-scanner
```

## Troubleshooting

### IBKR Connection Issues

- Make sure TWS or IB Gateway is running
- Verify API access is enabled
- Check that the port number matches (default is 7497 for paper trading)
- Ensure you're not exceeding the API call limits

### Data Issues

- If no data is returned, try a different symbol or timeframe
- For intraday timeframes, Yahoo Finance may have limitations
- IBKR data is more reliable but requires an active connection

### Scanner Not Running Continuously

- Check the logs in the `logs` directory
- Make sure the script is running with proper permissions
- For long-running sessions, consider using a process manager like `supervisord` 