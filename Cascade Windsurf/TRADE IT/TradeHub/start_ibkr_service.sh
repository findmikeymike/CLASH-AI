#!/bin/bash
# Autostart script for IBKR Aggregator Service
# This script ensures the IBKR service runs automatically,
# with error recovery and logging

# Change to the correct directory
cd "$(dirname "$0")"

# Configuration
LOG_DIR="logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/ibkr_service_${TIMESTAMP}.log"
MAX_RESTARTS=5
RESTART_DELAY=60  # seconds

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log function
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

# Make sure the service script is executable
chmod +x ibkr_aggregator_service.py

# Log startup
log "Starting IBKR Aggregator Service..."

# Check if TWS/IB Gateway is running
if ! lsof -i:7496 -sTCP:LISTEN > /dev/null 2>&1; then
    log "WARNING: IBKR TWS/Gateway doesn't appear to be running on port 7496"
    log "The service will attempt to connect when TWS/Gateway becomes available"
fi

# Run the service with restart capability
restart_count=0
while [ $restart_count -lt $MAX_RESTARTS ]; do
    log "Starting service (attempt $((restart_count+1))/$MAX_RESTARTS)"
    
    # Start the service and redirect output to log file
    python3 ibkr_aggregator_service.py "$@" 2>&1 | tee -a "$LOG_FILE"
    
    exit_code=$?
    if [ $exit_code -eq 0 ]; then
        log "Service exited normally with code $exit_code"
        break
    else
        restart_count=$((restart_count+1))
        log "Service crashed with exit code $exit_code, will restart in $RESTART_DELAY seconds..."
        sleep $RESTART_DELAY
    fi
done

if [ $restart_count -eq $MAX_RESTARTS ]; then
    log "ERROR: Maximum restart attempts ($MAX_RESTARTS) reached. Giving up."
    exit 1
fi

log "IBKR Aggregator Service terminated"
