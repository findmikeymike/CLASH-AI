"""
TradingView Lightweight Charts integration for the custom dashboard.
This module provides functions to create charts using lightweight-charts Python library.
"""

import os
import json
import pandas as pd
from lightweight_charts import Chart
from loguru import logger

def create_tradingview_chart(data_df, chart_title="Price Chart", width=800, height=400):
    """
    Create a TradingView Lightweight Chart from a pandas DataFrame.
    
    Args:
        data_df (pd.DataFrame): DataFrame with OHLCV data
        chart_title (str): Title of the chart
        width (int): Width of the chart
        height (int): Height of the chart
        
    Returns:
        str: HTML content for the chart
    """
    try:
        # Configure the chart
        chart = Chart(width=width, height=height)
        
        # Set chart options
        chart.layout(background_color='#1e222d', 
                     text_color='#d1d4dc',
                     watermark='Trade Hub')
        
        # Format data for TradingView
        formatted_data = data_df.copy()
        
        # Ensure time column is in the right format
        if 'time' not in formatted_data.columns:
            formatted_data['time'] = formatted_data.index
        
        # Set the data
        chart.set(formatted_data)
        
        # Generate HTML
        html_content = chart._repr_html_()
        
        return html_content
    
    except Exception as e:
        logger.error(f"Error creating TradingView chart: {e}")
        return f"<div class='error-message'>Error creating chart: {str(e)}</div>"

def create_order_flow_chart(data_df, width=800, height=300):
    """
    Create an order flow chart using TradingView Lightweight Charts.
    
    Args:
        data_df (pd.DataFrame): DataFrame with order flow data
        width (int): Width of the chart
        height (int): Height of the chart
        
    Returns:
        str: HTML content for the chart
    """
    try:
        # Configure the chart
        chart = Chart(width=width, height=height)
        
        # Set chart options
        chart.layout(background_color='#1e222d', 
                     text_color='#d1d4dc')
        
        # Format data for histogram
        chart.set(data_df)
        
        # Generate HTML
        html_content = chart._repr_html_()
        
        return html_content
    
    except Exception as e:
        logger.error(f"Error creating order flow chart: {e}")
        return f"<div class='error-message'>Error creating order flow chart: {str(e)}</div>" 