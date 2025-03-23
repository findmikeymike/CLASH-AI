"""
Trading Workflows - Prefect workflows for orchestrating trading agents.
"""

# Import workarounds for Prefect 3.x compatibility
try:
    # Try importing the 3.x compatible workflows first
    from .setup_scanner_v3 import setup_scanner_workflow
    from .market_analysis_v3 import market_analysis_workflow
    __all__ = ['setup_scanner_workflow', 'market_analysis_workflow']
except ImportError:
    # If 3.x compatible workflows are not available, don't import anything
    # This prevents errors when the old workflows try to import from prefect 2.x
    __all__ = [] 