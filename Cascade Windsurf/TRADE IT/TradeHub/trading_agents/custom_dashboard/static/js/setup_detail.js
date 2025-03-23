/**
 * Setup Detail View
 * 
 * This module handles the detailed view of a trading setup when a setup card is clicked.
 * It displays a larger chart and additional analysis from various agents.
 */

// Global variables
let currentSetupId = null;
let detailChart = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initSetupDetailView();
    console.log('Setup detail view initialized');
});

/**
 * Initialize the setup detail view
 */
function initSetupDetailView() {
    // Set up event listeners for closing the detail view
    document.getElementById('close-detail-view').addEventListener('click', closeDetailView);
}

/**
 * Show the setup detail view for a specific setup
 * @param {number} setupId - The ID of the setup to display
 */
function showSetupDetail(setupId) {
    currentSetupId = setupId;
    
    // Show the detail view container
    const detailContainer = document.getElementById('setup-detail-container');
    detailContainer.classList.add('active');
    
    // Clear any previous error
    document.getElementById('detail-error').style.display = 'none';
    document.getElementById('detail-error').textContent = '';
    
    // Fetch the setup data
    fetchSetupDetail(setupId);
}

/**
 * Fetch the setup detail data from the API
 * @param {number} setupId - The ID of the setup to fetch
 */
async function fetchSetupDetail(setupId) {
    try {
        // Show loading state
        document.getElementById('detail-loading').style.display = 'flex';
        document.getElementById('detail-error').style.display = 'none';
        
        console.log(`Fetching setup detail for ID: ${setupId}`);
        
        // Fetch the setup data
        const response = await fetch(`/api/setup/${setupId}`);
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`API error: ${response.status} ${response.statusText}`, errorText);
            throw new Error(`Failed to fetch setup detail: ${response.statusText}`);
        }
        
        // Parse the JSON response, with error handling
        let setupData;
        try {
            setupData = await response.json();
            console.log("Setup data received:", setupData);
        } catch (jsonError) {
            console.error("Failed to parse JSON response:", jsonError);
            throw new Error("Invalid response format from server");
        }
        
        // Check if we have the minimal required data
        if (!setupData || !setupData.symbol || !setupData.timeframe) {
            console.error("Missing required data in setup response", setupData);
            throw new Error("Incomplete setup data returned from server");
        }
        
        // Fetch price data for the chart
        console.log(`Fetching price data for ${setupData.symbol} (${setupData.timeframe})`);
        const priceResponse = await fetch(`/api/price-data/${setupData.symbol}?timeframe=${setupData.timeframe}`);
        if (!priceResponse.ok) {
            console.error(`Price data API error: ${priceResponse.status} ${priceResponse.statusText}`);
            throw new Error(`Failed to fetch price data: ${priceResponse.statusText}`);
        }
        
        // Parse the price data JSON, with error handling
        let priceData;
        try {
            priceData = await priceResponse.json();
            console.log(`Received ${priceData.length} price data points`);
        } catch (jsonError) {
            console.error("Failed to parse price data JSON:", jsonError);
            throw new Error("Invalid price data format from server");
        }
        
        // Check if we have any price data
        if (!priceData || !Array.isArray(priceData) || priceData.length === 0) {
            console.error("No valid price data received", priceData);
            // Create fallback price data
            priceData = createFallbackPriceData(setupData);
            console.log("Using fallback price data");
        }
        
        // Render the setup detail
        renderSetupDetail(setupData, priceData);
        
        // Hide loading state
        document.getElementById('detail-loading').style.display = 'none';
        
    } catch (error) {
        console.error('Error fetching setup detail:', error);
        document.getElementById('detail-loading').style.display = 'none';
        document.getElementById('detail-error').textContent = `Error: ${error.message}`;
        document.getElementById('detail-error').style.display = 'block';
    }
}

/**
 * Create fallback price data when the API doesn't return any
 * @param {Object} setupData - The setup data
 * @returns {Array} - Fallback price data
 */
function createFallbackPriceData(setupData) {
    const data = [];
    const basePrice = setupData.entry_price || 100;
    const now = new Date();
    
    // Create 30 data points around the entry price
    for (let i = 0; i < 30; i++) {
        const time = new Date(now);
        time.setDate(now.getDate() - 30 + i);
        
        const variance = 0.05; // 5% variance
        const factor = 1 + ((Math.random() * 2 - 1) * variance);
        const price = basePrice * factor;
        
        data.push({
            time: time.toISOString(),
            open: price * (1 + (Math.random() * 0.01)),
            high: price * (1 + (Math.random() * 0.02)),
            low: price * (1 - (Math.random() * 0.02)),
            close: price,
            volume: Math.floor(Math.random() * 1000000) + 500000
        });
    }
    
    return data;
}

/**
 * Render the setup detail view
 * @param {Object} setupData - The setup data
 * @param {Array} priceData - The price data for the chart
 */
function renderSetupDetail(setupData, priceData) {
    // Update the header information
    document.getElementById('detail-symbol').textContent = setupData.symbol;
    document.getElementById('detail-type').textContent = setupData.setup_type;
    document.getElementById('detail-timeframe').textContent = setupData.timeframe;
    
    // Set the direction badge
    const directionBadge = document.getElementById('detail-direction');
    directionBadge.textContent = setupData.direction.toUpperCase();
    directionBadge.className = `setup-direction ${setupData.direction.toLowerCase()}`;
    
    // Update the status badge
    const statusBadge = document.getElementById('detail-status');
    statusBadge.textContent = setupData.status.replace('_', ' ').toUpperCase();
    statusBadge.className = `status-badge ${setupData.status.toLowerCase()}`;
    
    // Update the market alignment badge
    const marketBadge = document.getElementById('market-aligned-badge');
    if (setupData.market_aligned !== undefined) {
        if (setupData.market_aligned) {
            marketBadge.className = 'market-badge aligned';
            marketBadge.innerHTML = '<i class="fas fa-check-circle"></i> Market Aligned';
        } else {
            marketBadge.className = 'market-badge misaligned';
            marketBadge.innerHTML = '<i class="fas fa-times-circle"></i> Market Misaligned';
        }
        marketBadge.style.display = 'flex';
    } else {
        marketBadge.style.display = 'none';
    }
    
    // Update the metrics
    document.getElementById('detail-entry').textContent = setupData.entry_price.toFixed(2);
    document.getElementById('detail-stop').textContent = setupData.stop_loss.toFixed(2);
    document.getElementById('detail-target').textContent = setupData.target.toFixed(2);
    document.getElementById('detail-risk-reward').textContent = setupData.risk_reward.toFixed(2);
    
    // Update the confidence score if available
    if (setupData.confidence !== undefined) {
        document.getElementById('detail-confidence').textContent = setupData.confidence.toFixed(1);
        document.getElementById('confidence-container').style.display = 'flex';
    } else {
        document.getElementById('confidence-container').style.display = 'none';
    }
    
    // Render the chart
    renderDetailChart(setupData, priceData);
    
    // Populate the agent outputs if analysis data is available
    if (setupData.analysis) {
        // If analysis data exists in the new format, use it
        document.getElementById('order-flow-content').style.display = 'block';
        document.getElementById('options-content').style.display = 'block';
        
        if (setupData.analysis.order_flow) {
            populateOrderFlowAnalysis(setupData);
        } else {
            document.getElementById('order-flow-content').innerHTML = '<p class="no-data">No order flow analysis available</p>';
        }
        
        if (setupData.analysis.options) {
            populateOptionsAnalysis(setupData);
        } else {
            document.getElementById('options-content').innerHTML = '<p class="no-data">No options analysis available</p>';
        }
    } else {
        // No analysis data available
        document.getElementById('order-flow-content').innerHTML = '<p class="no-data">No order flow analysis available</p>';
        document.getElementById('options-content').innerHTML = '<p class="no-data">No options analysis available</p>';
    }
}

/**
 * Format the price data for the chart
 * @param {Array} priceData - The raw price data
 * @returns {Array} - The formatted data for the chart
 */
function formatPriceDataForChart(priceData) {
    return priceData.map(d => {
        // Get the time value, supporting both 'time' and 'date' fields
        let timeValue;
        if (d.time) {
            timeValue = new Date(d.time).getTime() / 1000;
        } else if (d.date) {
            timeValue = new Date(d.date).getTime() / 1000;
        } else {
            // Fallback in case neither field is present
            timeValue = new Date().getTime() / 1000;
            console.warn('Price data point missing time/date field', d);
        }
        
        return {
            time: timeValue,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
        };
    });
}

/**
 * Render the detail chart
 * @param {Object} setupData - The setup data
 * @param {Array} priceData - The price data for the chart
 */
function renderDetailChart(setupData, priceData) {
    const chartContainer = document.getElementById('detail-chart');
    
    // Clear any existing chart
    if (detailChart) {
        detailChart.remove();
    }
    
    // Create a new chart
    detailChart = LightweightCharts.createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: 500,
        layout: {
            background: { color: '#1E222D' },
            textColor: '#D1D4DC',
        },
        grid: {
            vertLines: { color: '#2A2E39' },
            horzLines: { color: '#2A2E39' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
            vertLine: {
                width: 1,
                color: '#2962FF',
                style: LightweightCharts.LineStyle.Dashed,
            },
            horzLine: {
                width: 1,
                color: '#2962FF',
                style: LightweightCharts.LineStyle.Dashed,
            },
        },
        timeScale: {
            borderColor: '#363A45',
            timeVisible: true,
        },
        rightPriceScale: {
            borderColor: '#363A45',
        },
    });
    
    // Add a candlestick series
    const candlestickSeries = detailChart.addCandlestickSeries({
        upColor: '#26A69A',
        downColor: '#EF5350',
        borderVisible: false,
        wickUpColor: '#26A69A',
        wickDownColor: '#EF5350',
    });
    
    // Format the price data for the chart
    const formattedData = formatPriceDataForChart(priceData);
    
    // Set the data
    candlestickSeries.setData(formattedData);
    
    // Add markers for entry, stop, and target
    const markers = [];
    
    // Entry marker
    if (formattedData.length > 0) {
        markers.push({
            time: formattedData[formattedData.length - 1].time,
            position: 'inBar',
            color: '#2962FF',
            shape: 'circle',
            text: 'Entry',
            size: 1,
        });
    }
    
    // Add price lines for entry, stop, and target
    const entryLine = candlestickSeries.createPriceLine({
        price: setupData.entry_price,
        color: '#2962FF',
        lineWidth: 2,
        lineStyle: LightweightCharts.LineStyle.Solid,
        axisLabelVisible: true,
        title: 'Entry',
    });
    
    const stopLine = candlestickSeries.createPriceLine({
        price: setupData.stop_loss,
        color: '#EF5350',
        lineWidth: 2,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: 'Stop',
    });
    
    const targetLine = candlestickSeries.createPriceLine({
        price: setupData.target,
        color: '#26A69A',
        lineWidth: 2,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: 'Target',
    });
    
    // Add markers
    candlestickSeries.setMarkers(markers);
    
    // Fit the content
    detailChart.timeScale().fitContent();
    
    // Handle window resize
    window.addEventListener('resize', () => {
        if (detailChart) {
            detailChart.resize(chartContainer.clientWidth, 500);
        }
    });
}

/**
 * Populate the market analysis tab
 * @param {Object} setupData - The setup data
 */
function populateMarketAnalysis(setupData) {
    const container = document.getElementById('market-analysis-content');
    
    // Clear the container
    container.innerHTML = '';
    
    // Check if market analysis data is available
    if (!setupData.market_analysis) {
        container.innerHTML = '<p class="no-data">No market analysis data available</p>';
        return;
    }
    
    // Create the market analysis content
    const marketAnalysis = setupData.market_analysis;
    
    // Create the market trend section
    const trendSection = document.createElement('div');
    trendSection.className = 'analysis-section';
    trendSection.innerHTML = `
        <h3>Market Trend</h3>
        <div class="trend-indicator ${marketAnalysis.trend.toLowerCase()}">
            <i class="fas fa-${marketAnalysis.trend === 'bullish' ? 'arrow-up' : 'arrow-down'}"></i>
            <span>${marketAnalysis.trend.toUpperCase()}</span>
        </div>
        <p>Market strength: <strong>${marketAnalysis.strength.toFixed(2)}</strong></p>
        <p>Volatility: <strong>${marketAnalysis.volatility.toFixed(4)}</strong></p>
    `;
    
    // Create the confluence section
    const confluenceSection = document.createElement('div');
    confluenceSection.className = 'analysis-section';
    confluenceSection.innerHTML = `
        <h3>Setup Confluence</h3>
        <div class="confluence-meter">
            <div class="confluence-bar" style="width: ${setupData.confluence_score}%"></div>
            <span class="confluence-value">${setupData.confluence_score}%</span>
        </div>
        <p>Market aligned: <strong>${setupData.market_aligned ? 'Yes' : 'No'}</strong></p>
    `;
    
    // Add the sections to the container
    container.appendChild(trendSection);
    container.appendChild(confluenceSection);
}

/**
 * Populate the order flow analysis agent output
 * @param {Object} setupData - The setup data
 */
function populateOrderFlowAnalysis(setupData) {
    const container = document.getElementById('order-flow-content');
    
    // Clear the container
    container.innerHTML = '';
    
    // Get the order flow data from the new structure
    const orderFlowData = setupData.analysis?.order_flow || setupData.order_flow_analysis;
    
    // Check if order flow analysis data is available
    if (!orderFlowData) {
        container.innerHTML = '<p class="no-data">No order flow analysis available</p>';
        return;
    }
    
    // Create the agent data display
    // Create a compact data view
    const dataContainer = document.createElement('div');
    dataContainer.className = 'agent-data';
    
    // Add key metrics, handling both potential data structures
    const metrics = [
        { label: 'Buying Pressure', value: orderFlowData.buying_pressure !== undefined ? orderFlowData.buying_pressure.toFixed(1) + '%' : null },
        { label: 'Selling Pressure', value: orderFlowData.selling_pressure !== undefined ? orderFlowData.selling_pressure.toFixed(1) + '%' : null },
        { label: 'Smart Money', value: orderFlowData.smart_money_direction || null },
        { label: 'Imbalance', value: orderFlowData.imbalance !== undefined ? orderFlowData.imbalance.toFixed(1) : null }
    ];
    
    // Add metrics to the container
    metrics.forEach(metric => {
        if (metric.value) {
            const item = document.createElement('div');
            item.className = 'agent-data-item';
            item.innerHTML = `
                <span class="agent-data-label">${metric.label}</span>
                <span class="agent-data-value">${metric.value}</span>
            `;
            dataContainer.appendChild(item);
        }
    });
    
    container.appendChild(dataContainer);
}

/**
 * Populate the options analysis agent output
 * @param {Object} setupData - The setup data
 */
function populateOptionsAnalysis(setupData) {
    const container = document.getElementById('options-content');
    
    // Clear the container
    container.innerHTML = '';
    
    // Get the options data from the new structure
    const optionsData = setupData.analysis?.options || setupData.options_analysis;
    
    // Check if options analysis data is available
    if (!optionsData) {
        container.innerHTML = '<p class="no-data">No options analysis available</p>';
        return;
    }
    
    // Create the agent data display
    // Create a compact data view
    const dataContainer = document.createElement('div');
    dataContainer.className = 'agent-data';
    
    // Add key metrics, handling both potential data structures
    const metrics = [
        { label: 'IV Percentile', value: optionsData.iv_percentile !== undefined ? optionsData.iv_percentile.toFixed(1) + '%' : null },
        { label: 'Put/Call Ratio', value: optionsData.put_call_ratio !== undefined ? optionsData.put_call_ratio.toFixed(2) : null },
        { label: 'Unusual Activity', value: optionsData.unusual_activity !== undefined ? (optionsData.unusual_activity ? 'Yes' : 'No') : null },
        { label: 'Call OI', value: optionsData.open_interest?.calls ? optionsData.open_interest.calls.toLocaleString() : null },
        { label: 'Put OI', value: optionsData.open_interest?.puts ? optionsData.open_interest.puts.toLocaleString() : null }
    ];
    
    // Add metrics to the container
    metrics.forEach(metric => {
        if (metric.value) {
            const item = document.createElement('div');
            item.className = 'agent-data-item';
            item.innerHTML = `
                <span class="agent-data-label">${metric.label}</span>
                <span class="agent-data-value">${metric.value}</span>
            `;
            dataContainer.appendChild(item);
        }
    });
    
    container.appendChild(dataContainer);
}

/**
 * Show a specific tab content
 * @param {string} tabId - The ID of the tab to show
 */
function showTabContent(tabId) {
    // This function is no longer needed since we're displaying all content in rows
    // But we'll keep it for backward compatibility
    console.log(`Tab function called for '${tabId}' but all sections are now displayed in rows`);
}

/**
 * Close the detail view
 */
function closeDetailView() {
    const detailContainer = document.getElementById('setup-detail-container');
    detailContainer.classList.remove('active');
    
    // Clear the current setup ID
    currentSetupId = null;
    
    // Remove the chart
    if (detailChart) {
        detailChart.remove();
        detailChart = null;
    }
}

// Export the functions to global scope
window.showSetupDetail = showSetupDetail;
window.closeDetailView = closeDetailView;

// Also export as an object for module-style imports
window.setupDetail = {
    initSetupDetailView,
    showSetupDetail,
    closeDetailView
}; 