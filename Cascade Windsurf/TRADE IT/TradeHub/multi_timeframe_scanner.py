import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Timeframe Market Scanner")
    parser.add_argument("--symbols", nargs="+", required=True, help="Symbols to scan")
    parser.add_argument("--timeframes", nargs="+", required=True, help="Timeframes to scan")
    parser.add_argument("--interval", type=int, default=5, help="Interval between scans in minutes")
    parser.add_argument("--duration", default="1 M", help="How far back to fetch data")
    parser.add_argument("--scan-outside-market-hours", action="store_true", help="Scan outside market hours")
    parser.add_argument("--max-scans", type=int, help="Maximum number of scans to run")
    
    args = parser.parse_args()
    
    start_multi_timeframe_scanner(
        args.symbols,
        args.timeframes,
        interval_minutes=args.interval,
        duration=args.duration,
        scan_outside_market_hours=args.scan_outside_market_hours,
        max_scans=args.max_scans
    ) 