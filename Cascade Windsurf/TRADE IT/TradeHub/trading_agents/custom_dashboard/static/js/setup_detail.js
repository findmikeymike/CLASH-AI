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
    
    // Initialize the detail view UI elements
    initDetailView();
}

/**
 * Initialize the detail view UI elements
 */
function initDetailView() {
    console.log("Initializing detail view UI...");
    
    // Setup close button
    const closeBtn = document.getElementById('close-detail-view');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeDetailView);
    }
    
    // Setup Join the Party button
    const joinPartyBtn = document.querySelector('.join-party-btn');
    if (joinPartyBtn) {
        joinPartyBtn.addEventListener('click', function() {
            console.log("Joining the party!");
            // Toggle class for visual feedback
            this.classList.toggle('joined');
            
            // Get the current setup ID
            const currentSetupId = document.querySelector('.detail-content').getAttribute('data-setup-id');
            
            if (this.classList.contains('joined')) {
                this.innerHTML = '<i class="fas fa-glass-cheers"></i> Party Joined!';
                
                // Update the corresponding card button
                const card = document.querySelector(`.setup-card[data-setup-id="${currentSetupId}"]`);
                if (card) {
                    const cardBtn = card.querySelector('.setup-action-btn.party-btn');
                    if (cardBtn) {
                        cardBtn.classList.add('joined');
                        cardBtn.innerHTML = '<i class="fas fa-users"></i> Joined';
                        cardBtn.style.background = 'linear-gradient(135deg, #4338ca, #3b82f6)';
                        cardBtn.style.color = 'white';
                    }
                }
                
                // Show the comment feed
                const commentFeed = document.querySelector('.detail-comment-feed-placeholder');
                if (commentFeed) {
                    commentFeed.innerHTML = '<div class="comment-feed-header">Party Chat</div><div class="comment-feed-messages"></div><div class="comment-feed-input"><input type="text" placeholder="Type your message..." disabled><button disabled>Send</button></div>';
                    commentFeed.classList.add('active');
                }
            } else {
                this.innerHTML = '<i class="fas fa-glass-cheers"></i> Join the Party';
                
                // Update the corresponding card button
                const card = document.querySelector(`.setup-card[data-setup-id="${currentSetupId}"]`);
                if (card) {
                    const cardBtn = card.querySelector('.setup-action-btn.party-btn');
                    if (cardBtn) {
                        cardBtn.classList.remove('joined');
                        cardBtn.innerHTML = '<i class="fas fa-users"></i> Join the Party';
                        cardBtn.style.background = 'linear-gradient(135deg, #6e57ff, #3b82f6)';
                        cardBtn.style.color = 'white';
                    }
                }
                
                // Reset the comment feed
                const commentFeed = document.querySelector('.detail-comment-feed-placeholder');
                if (commentFeed) {
                    commentFeed.innerHTML = '';
                    commentFeed.classList.remove('active');
                }
            }
        });
    }
    
    // Setup thumbs down button
    const thumbsDownBtn = document.querySelector('.thumbs-down-btn');
    if (thumbsDownBtn) {
        thumbsDownBtn.addEventListener('click', function() {
            this.classList.toggle('active');
        });
    }
}

/**
 * Show the setup detail view for a specific setup
 * @param {number} setupId - The ID of the setup to display
 * @param {Object} setupData - Optional setup data object. If provided, we'll use this instead of making an API call
 */
function showSetupDetail(setupId, setupData = null) {
    console.log(`Showing detail for setup: ${setupId}`);
    
    // Show loading state
    const detailContainer = document.getElementById('setup-detail-container');
    const loadingIndicator = document.getElementById('detail-loading');
    const errorDisplay = document.getElementById('detail-error');
    
    if (!detailContainer || !loadingIndicator || !errorDisplay) {
        console.error('Required DOM elements not found for setup detail view');
        return;
    }
    
    detailContainer.classList.add('active');
    loadingIndicator.style.display = 'flex';
    errorDisplay.style.display = 'none';
    
    try {
        // If setup data was passed directly, use it instead of fetching
        if (setupData) {
            console.log('Using provided setup data:', setupData);
            fetchPriceDataAndRender(setupData);
            
            // Set the party button state based on the isPartyJoined flag
            const joinPartyBtn = document.querySelector('.join-party-btn');
            if (joinPartyBtn && setupData.isPartyJoined) {
                joinPartyBtn.classList.add('joined');
                joinPartyBtn.innerHTML = '<i class="fas fa-glass-cheers"></i> Party Joined!';
                
                // Show the comment feed if the party is joined
                const commentFeed = document.querySelector('.detail-comment-feed-placeholder');
                if (commentFeed) {
                    commentFeed.innerHTML = '<div class="comment-feed-header">Party Chat</div><div class="comment-feed-messages"></div><div class="comment-feed-input"><input type="text" placeholder="Type your message..." disabled><button disabled>Send</button></div>';
                    commentFeed.classList.add('active');
                }
            }
        } else {
            // Otherwise fetch the data from the API
            console.log('Fetching setup data from API...');
            fetchSetupDetail(setupId);
        }
    } catch (error) {
        console.error('Error showing setup detail:', error);
    }
}

/**
 * Fetch price data and render the setup detail view
 * @param {Object} setupData - The setup data 
 * @param {string} timeframe - Optional timeframe override
 */
async function fetchPriceDataAndRender(setupData, timeframe = null) {
    try {
        // Show loading state
        document.getElementById('detail-loading').style.display = 'flex';
        document.getElementById('detail-error').style.display = 'none';
        
        // Check if we have the minimal required data
        if (!setupData || !setupData.symbol || !setupData.timeframe) {
            console.error("Missing required data in setup", setupData);
            throw new Error("Incomplete setup data provided");
        }
        
        // Use provided timeframe or fall back to the setup's default timeframe
        const requestTimeframe = timeframe || setupData.timeframe;
        
        // Fetch price data for the chart
        console.log(`Fetching price data for ${setupData.symbol} (${requestTimeframe})`);
        const priceResponse = await fetch(`/api/price-data/${setupData.symbol}?timeframe=${requestTimeframe}`);
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
            console.log("Using fallback price data", priceData);
        }
        
        // Hide the loading indicator
        document.getElementById('detail-loading').style.display = 'none';
        
        // Store the current timeframe in the global state
        setupData.currentTimeframe = requestTimeframe;
        
        // Render the setup detail
        renderSetupDetail(setupData, priceData);
        
    } catch (error) {
        // Hide the loading indicator
        document.getElementById('detail-loading').style.display = 'none';
        
        // Show the error message
        const errorElement = document.getElementById('detail-error');
        errorElement.textContent = `Error: ${error.message}`;
        errorElement.style.display = 'block';
        
        console.error("Failed to fetch price data and render setup detail:", error);
    }
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
        
        // Once we have the setup data, fetch price data and render
        fetchPriceDataAndRender(setupData);
        
    } catch (error) {
        // Hide the loading indicator
        document.getElementById('detail-loading').style.display = 'none';
        
        // Show the error message
        const errorElement = document.getElementById('detail-error');
        errorElement.textContent = `Error: ${error.message}`;
        errorElement.style.display = 'block';
        
        console.error("Failed to fetch setup detail:", error);
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
    // Update the symbol in the detail view
    document.getElementById('detail-symbol').textContent = setupData.symbol || 'Unknown Symbol';
    
    // Update the pattern type
    let patternType = setupData.pattern_type || 'Unknown Pattern';
    patternType = patternType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    document.getElementById('detail-type').textContent = patternType;
    
    // Update the direction with appropriate styling
    const directionElement = document.getElementById('detail-direction');
    const direction = (setupData.direction || '').toLowerCase();
    const isBullish = direction.includes('bull');
    directionElement.innerHTML = `<i class="fas fa-arrow-${isBullish ? 'up' : 'down'}"></i> ${isBullish ? 'Bullish' : 'Bearish'}`;
    directionElement.className = `setup-direction ${isBullish ? 'bullish' : 'bearish'}`;
    
    // Update the timeframe display
    document.getElementById('detail-timeframe').textContent = setupData.currentTimeframe || setupData.timeframe || '1D';
    
    // Add or update the timeframe selector
    createTimeframeSelector(setupData);
    
    // Render the chart
    renderDetailChart(setupData, priceData);
    
    // Populate metrics section
    const entryPrice = parseFloat(setupData.entry_price) || 0;
    const stopLoss = parseFloat(setupData.stop_loss) || 0;
    const target = parseFloat(setupData.target) || 0;
    
    document.getElementById('detail-entry').textContent = `$${entryPrice.toFixed(2)}`;
    document.getElementById('detail-target').textContent = `$${target.toFixed(2)}`;
    document.getElementById('detail-stop').textContent = `$${stopLoss.toFixed(2)}`;
    
    // Calculate and update risk-reward ratio
    let riskReward = 0;
    try {
        if (stopLoss !== entryPrice) {
            riskReward = Math.abs(target - entryPrice) / Math.abs(stopLoss - entryPrice);
        }
    } catch (error) {
        console.error('Error calculating R:R ratio:', error);
    }
    document.getElementById('detail-risk-reward-ratio').textContent = `${riskReward.toFixed(2)}x`;
    
    // Update status and market aligned badge if they exist
    const statusBadge = document.getElementById('detail-status');
    if (statusBadge && setupData.status) {
        statusBadge.textContent = setupData.status.replace('_', ' ').toUpperCase();
        statusBadge.className = `status-badge ${setupData.status.toLowerCase()}`;
    }
    
    const marketBadge = document.getElementById('market-aligned-badge');
    if (marketBadge && setupData.market_aligned !== undefined) {
        if (setupData.market_aligned) {
            marketBadge.className = 'market-badge aligned';
            marketBadge.innerHTML = '<i class="fas fa-check-circle"></i> Market Aligned';
        } else {
            marketBadge.className = 'market-badge misaligned';
            marketBadge.innerHTML = '<i class="fas fa-times-circle"></i> Market Misaligned';
        }
        marketBadge.style.display = 'flex';
    } else if (marketBadge) {
        marketBadge.style.display = 'none';
    }
    
    // Update confidence score if available
    if (setupData.confidence !== undefined) {
        const confidenceElement = document.getElementById('detail-confidence');
        const confidenceContainer = document.getElementById('confidence-container');
        if (confidenceElement) {
            confidenceElement.textContent = setupData.confidence.toFixed(1);
        }
        if (confidenceContainer) {
            confidenceContainer.style.display = 'flex';
        }
    } else {
        const confidenceContainer = document.getElementById('confidence-container');
        if (confidenceContainer) {
            confidenceContainer.style.display = 'none';
        }
    }
    
    // Populate analysis tabs if analysis data is available
    if (setupData.analysis) {
        if (setupData.analysis.market) {
            populateMarketAnalysis(setupData);
        } else {
            const marketContent = document.getElementById('market-content');
            if (marketContent) {
                marketContent.innerHTML = '<p class="no-data">No market analysis available</p>';
            }
        }
        
        if (setupData.analysis.order_flow) {
            populateOrderFlowAnalysis(setupData);
        } else {
            const orderFlowContent = document.getElementById('order-flow-content');
            if (orderFlowContent) {
                orderFlowContent.innerHTML = '<p class="no-data">No order flow analysis available</p>';
            }
        }
        
        if (setupData.analysis.options) {
            populateOptionsAnalysis(setupData);
        } else {
            const optionsContent = document.getElementById('options-content');
            if (optionsContent) {
                optionsContent.innerHTML = '<p class="no-data">No options analysis available</p>';
            }
        }
    } else {
        // No analysis data available
        const orderFlowContent = document.getElementById('order-flow-content');
        const optionsContent = document.getElementById('options-content');
        const marketContent = document.getElementById('market-content');
        
        if (orderFlowContent) {
            orderFlowContent.innerHTML = '<p class="no-data">No order flow analysis available</p>';
        }
        if (optionsContent) {
            optionsContent.innerHTML = '<p class="no-data">No options analysis available</p>';
        }
        if (marketContent) {
            marketContent.innerHTML = '<p class="no-data">No market analysis available</p>';
        }
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
 * Create or update the timeframe selector
 * @param {Object} setupData - The setup data
 */
function createTimeframeSelector(setupData) {
    const timeframeContainer = document.getElementById('timeframe-selector-container');
    if (!timeframeContainer) {
        // Create the container if it doesn't exist
        const chartHeaderDiv = document.querySelector('.detail-chart-header');
        if (chartHeaderDiv) {
            const container = document.createElement('div');
            container.id = 'timeframe-selector-container';
            container.className = 'timeframe-selector-container';
            
            // Create a label for the dropdown
            const label = document.createElement('label');
            label.textContent = 'Timeframe: ';
            label.htmlFor = 'timeframe-selector';
            container.appendChild(label);
            
            // Create the dropdown
            const select = document.createElement('select');
            select.id = 'timeframe-selector';
            select.className = 'timeframe-selector';
            
            // Add timeframe options
            const timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M'];
            timeframes.forEach(tf => {
                const option = document.createElement('option');
                option.value = tf;
                option.textContent = tf.toUpperCase();
                // Set the current timeframe as selected
                if (tf === (setupData.currentTimeframe || setupData.timeframe)) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
            
            // Add change event listener
            select.addEventListener('change', function() {
                const newTimeframe = this.value;
                console.log(`Changing timeframe to ${newTimeframe}`);
                // Re-fetch price data with the new timeframe
                fetchPriceDataAndRender(setupData, newTimeframe);
            });
            
            container.appendChild(select);
            chartHeaderDiv.appendChild(container);
        }
    } else {
        // Update the existing selector
        const select = document.getElementById('timeframe-selector');
        if (select) {
            // Update the selected option
            const options = select.querySelectorAll('option');
            options.forEach(option => {
                option.selected = option.value === (setupData.currentTimeframe || setupData.timeframe);
            });
        }
    }
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