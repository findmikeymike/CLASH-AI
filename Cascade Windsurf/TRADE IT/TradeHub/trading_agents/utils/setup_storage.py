"""
Setup storage utility for storing and retrieving trading setups.
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3
from loguru import logger

# Define the path for the database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "setups.db")

# Ensure the data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    """Initialize the database with the required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create setups table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS setups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        setup_type TEXT NOT NULL,
        direction TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        confidence REAL,
        entry_price REAL,
        stop_loss REAL,
        target REAL,
        risk_reward REAL,
        date_identified TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        metadata TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Setup database initialized")

def store_setup(setup: Dict[str, Any]) -> int:
    """
    Store a trading setup in the database.
    
    Args:
        setup: A dictionary containing setup details
        
    Returns:
        The ID of the stored setup
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure the setup has a date_identified field
    if "date_identified" not in setup:
        setup["date_identified"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Convert metadata to JSON if present
    if "metadata" in setup and isinstance(setup["metadata"], dict):
        setup["metadata"] = json.dumps(setup["metadata"])
    
    # Insert the setup
    columns = ", ".join(setup.keys())
    placeholders = ", ".join(["?" for _ in setup.keys()])
    values = tuple(setup.values())
    
    cursor.execute(f"INSERT INTO setups ({columns}) VALUES ({placeholders})", values)
    setup_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    logger.info(f"Stored setup {setup_id} for {setup.get('symbol')} ({setup.get('setup_type')})")
    return setup_id

def get_setup_by_id(setup_id: int) -> Dict[str, Any]:
    """
    Retrieve a specific trading setup by its ID.
    
    Args:
        setup_id: The ID of the setup to retrieve
        
    Returns:
        A dictionary containing the setup details or None if not found
        
    Raises:
        ValueError: If the setup with the given ID is not found
    """
    logger.info(f"Fetching setup ID {setup_id} from database")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    # Query the setup
    cursor.execute("SELECT * FROM setups WHERE id = ?", (setup_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        logger.error(f"Setup with ID {setup_id} not found in database")
        raise ValueError(f"Setup with ID {setup_id} not found")
    
    # Convert row to dictionary safely
    try:
        setup = dict(row)
        logger.debug(f"Raw setup data from database: {setup}")
    except Exception as e:
        conn.close()
        logger.error(f"Error converting row to dictionary: {str(e)}")
        raise ValueError(f"Error retrieving setup details: {str(e)}")
    
    # Ensure all values are JSON serializable
    for key, value in setup.items():
        # Convert any SQLite specific types to standard Python types
        if isinstance(value, (bytes, bytearray)):
            try:
                setup[key] = value.decode('utf-8')
            except Exception as e:
                logger.warning(f"Unable to decode bytes for key {key}: {str(e)}")
                setup[key] = str(value)
        elif value is None:
            continue
        elif not isinstance(value, (str, int, float, bool, list, dict, tuple)):
            # If not a standard JSON serializable type, convert to string
            setup[key] = str(value)
    
    # Parse metadata JSON if present
    if setup.get("metadata"):
        try:
            setup["metadata"] = json.loads(setup["metadata"])
            logger.debug(f"Parsed metadata: {setup['metadata']}")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse metadata JSON: {e}")
            setup["metadata"] = {}
    
    # Add additional fields for the detail view
    setup["market_aligned"] = True  # This would be calculated based on market conditions
    
    # Add analysis data specific to this setup
    # In a real implementation, this would be fetched from your analysis database
    setup["analysis"] = {
        "options": {
            "iv_percentile": round(float(setup_id) * 0.1 % 100, 2),
            "put_call_ratio": round(1.0 + float(setup_id) * 0.01 % 1.5, 2),
            "unusual_activity": setup_id % 3 == 0
        },
        "order_flow": {
            "buying_pressure": round(float(setup_id) * 0.2 % 100, 2),
            "selling_pressure": round(float(setup_id) * 0.15 % 100, 2),
            "smart_money_direction": "bullish" if setup_id % 2 == 0 else "bearish"
        }
    }
    
    logger.debug(f"Added analysis data: {setup['analysis']}")
    
    conn.close()
    
    logger.info(f"Successfully retrieved setup {setup_id} from database")
    return setup

def get_setups(
    setup_type: Optional[str] = None,
    direction: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Retrieve trading setups from the database with optional filtering.
    
    Args:
        setup_type: Filter by setup type
        direction: Filter by direction (bullish/bearish)
        symbol: Filter by symbol
        timeframe: Filter by timeframe
        status: Filter by status
        limit: Maximum number of setups to return
        
    Returns:
        A list of setup dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    # Build the query with filters
    query = "SELECT * FROM setups WHERE 1=1"
    params = []
    
    if setup_type and setup_type != "all":
        query += " AND setup_type = ?"
        params.append(setup_type)
    
    if direction and direction != "all":
        query += " AND direction = ?"
        params.append(direction)
    
    if symbol:
        query += " AND symbol = ?"
        params.append(symbol)
    
    if timeframe:
        query += " AND timeframe = ?"
        params.append(timeframe)
    
    if status:
        query += " AND status = ?"
        params.append(status)
    
    # Order by date identified (newest first)
    query += " ORDER BY date_identified DESC LIMIT ?"
    params.append(limit)
    
    # Execute the query
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    # Convert rows to dictionaries
    setups = []
    for row in rows:
        setup = dict(row)
        
        # Parse metadata JSON if present
        if setup.get("metadata"):
            try:
                setup["metadata"] = json.loads(setup["metadata"])
            except json.JSONDecodeError:
                setup["metadata"] = {}
        
        setups.append(setup)
    
    conn.close()
    
    logger.info(f"Retrieved {len(setups)} setups from database")
    return setups

def update_setup_status(setup_id: int, status: str) -> bool:
    """
    Update the status of a trading setup.
    
    Args:
        setup_id: The ID of the setup to update
        status: The new status (active, triggered, expired, completed)
        
    Returns:
        True if the update was successful, False otherwise
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE setups SET status = ? WHERE id = ?", (status, setup_id))
    success = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    if success:
        logger.info(f"Updated setup {setup_id} status to {status}")
    else:
        logger.warning(f"Failed to update setup {setup_id} status")
    
    return success

# Initialize the database when the module is imported
init_db() 