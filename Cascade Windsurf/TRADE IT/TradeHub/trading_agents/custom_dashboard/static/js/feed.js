/**
 * Trade Hub - Setup Feed JavaScript
 * Handles the trade setup feed and mini-charts
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize mini charts
    initMiniCharts();
    
    // Setup event listeners
    setupEventListeners();
    
    // Fetch initial setups
    fetchSetups();
    
    // Initialize market overview panel
    initMarketOverviewPanel();
});

/**
 * Initialize the market overview panel with toggle functionality
 */
function initMarketOverviewPanel() {
    const toggleButton = document.querySelector('.toggle-market-detail');
    const detailView = document.querySelector('.market-detail-view');
    
    if (toggleButton && detailView) {
        toggleButton.addEventListener('click', function() {
            // Toggle active class on button
            this.classList.toggle('active');
            
            // Toggle active class on detail view
            detailView.classList.toggle('active');
            
            // Update icon
            const icon = this.querySelector('i');
            if (detailView.classList.contains('active')) {
                icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
            } else {
                icon.classList.replace('fa-chevron-up', 'fa-chevron-down');
            }
        });
    }
}

/**
 * Initialize mini charts for each setup card
 */
function initMiniCharts() {
    // Sample data for demonstration
    const sampleData = {
        'miniChart1': createSampleData('bullish', 30), // Increased data points for better visualization
        'miniChart2': createSampleData('bullish', 40),
        'miniChart3': createSampleData('bearish', 35)
    };
    
    // Initialize each mini chart
    Object.keys(sampleData).forEach(chartId => {
        const chartElement = document.getElementById(chartId);
        if (!chartElement) return;
        
        const chart = LightweightCharts.createChart(chartElement, {
            width: chartElement.parentElement.clientWidth - 10, // Use almost full width of parent
            height: 225, // Match CSS height
            layout: {
                background: { color: '#1E222D' },
                textColor: '#d1d4dc',
                fontSize: 12,
                fontFamily: 'Inter, sans-serif',
            },
            grid: {
                vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
                horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
            },
            rightPriceScale: {
                borderColor: 'rgba(197, 203, 206, 0.4)',
                visible: true,
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.2 // More space for volume
                }
            },
            timeScale: {
                borderColor: 'rgba(197, 203, 206, 0.4)',
                timeVisible: true,
                secondsVisible: false,
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    color: '#758696',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                },
                horzLine: {
                    color: '#758696',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                    labelBackgroundColor: '#758696',
                },
            },
        });
        
        // Store chart reference on the element for resize handling
        chartElement.chart = chart;
        
        // Add candlestick series
        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });
        
        // Set candlestick data
        candlestickSeries.setData(sampleData[chartId]);
        
        // Add volume series
        const volumeSeries = chart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: 'volume',
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
        });
        
        // Set volume data
        volumeSeries.setData(formatVolumeData(sampleData[chartId]));
        
        // Hide the volume price scale
        chart.priceScale('volume').applyOptions({
            scaleMargins: {
                top: 0.8,
                bottom: 0,
            },
            visible: false,
        });
        
        // Add indicators based on setup type
        if (chartId === 'miniChart1') {
            // Add EMA 20 for bullish flag
            addEMA(chart, sampleData[chartId], 20, '#2962FF');
            
            // Add entry marker (breakout point)
            const lastIndex = sampleData[chartId].length - 1;
            const breakoutPoint = sampleData[chartId][lastIndex - 4];
            
            const markerSeries = chart.addLineSeries({
                lastValueVisible: false,
                priceLineVisible: false,
            });
            
            markerSeries.setMarkers([
                {
                    time: breakoutPoint.time,
                    position: 'aboveBar',
                    color: '#26a69a',
                    shape: 'arrowUp',
                    text: 'Entry',
                    size: 2
                }
            ]);
        }
        
        if (chartId === 'miniChart2') {
            // Add SMA 50 for support bounce
            addSMA(chart, sampleData[chartId], 50, '#FF9800');
            
            // Add support line
            const supportSeries = chart.addLineSeries({
                color: 'rgba(76, 175, 80, 0.5)',
                lineWidth: 2,
                lineStyle: 2, // LightweightCharts.LineStyle.Dashed
                lastValueVisible: false,
            });
            
            const supportPrice = sampleData[chartId][sampleData[chartId].length - 10].low;
            supportSeries.setData([
                { time: sampleData[chartId][0].time, value: supportPrice },
                { time: sampleData[chartId][sampleData[chartId].length - 1].time, value: supportPrice }
            ]);
            
            // Add entry marker
            const lastIndex = sampleData[chartId].length - 1;
            const entryPoint = sampleData[chartId][lastIndex - 5];
            
            const markerSeries = chart.addLineSeries({
                lastValueVisible: false,
                priceLineVisible: false,
            });
            
            markerSeries.setMarkers([
                {
                    time: entryPoint.time,
                    position: 'aboveBar',
                    color: '#26a69a',
                    shape: 'arrowUp',
                    text: 'Entry',
                    size: 2
                }
            ]);
        }
        
        if (chartId === 'miniChart3') {
            // Add double top lines for bearish setup
            const topSeries = chart.addLineSeries({
                color: 'rgba(239, 83, 80, 0.5)',
                lineWidth: 2,
                lineStyle: 2, // LightweightCharts.LineStyle.Dashed
                lastValueVisible: false,
            });
            
            // Find the two tops
            const data = sampleData[chartId];
            let firstTop = data[0];
            let secondTop = data[0];
            
            for (let i = 5; i < data.length - 10; i++) {
                if (data[i].high > firstTop.high) {
                    firstTop = data[i];
                }
            }
            
            for (let i = data.length - 10; i < data.length; i++) {
                if (data[i].high > secondTop.high) {
                    secondTop = data[i];
                }
            }
            
            // Draw horizontal line at the top
            const topPrice = Math.max(firstTop.high, secondTop.high);
            topSeries.setData([
                { time: data[0].time, value: topPrice },
                { time: data[data.length - 1].time, value: topPrice }
            ]);
            
            // Draw neckline at the low between tops
            const necklineSeries = chart.addLineSeries({
                color: 'rgba(239, 83, 80, 0.3)',
                lineWidth: 2,
                lineStyle: 2, // LightweightCharts.LineStyle.Dashed
                lastValueVisible: false,
            });
            
            // Find the low between the tops
            let lowest = firstTop;
            const firstTopIndex = data.indexOf(firstTop);
            const secondTopIndex = data.indexOf(secondTop);
            
            for (let i = firstTopIndex; i < secondTopIndex; i++) {
                if (data[i].low < lowest.low) {
                    lowest = data[i];
                }
            }
            
            necklineSeries.setData([
                { time: data[0].time, value: lowest.low },
                { time: data[data.length - 1].time, value: lowest.low }
            ]);
            
            // Add entry marker (breakdown point)
            const lastIndex = data.length - 1;
            const breakdownPoint = data[lastIndex - 3];
            
            const markerSeries = chart.addLineSeries({
                lastValueVisible: false,
                priceLineVisible: false,
            });
            
            markerSeries.setMarkers([
                {
                    time: breakdownPoint.time,
                    position: 'belowBar',
                    color: '#ef5350',
                    shape: 'arrowDown',
                    text: 'Entry',
                    size: 2
                }
            ]);
        }
        
        // Fit content to the chart
        chart.timeScale().fitContent();
    });
}

/**
 * Create sample candlestick data for demo charts
 */
function createSampleData(trend, numCandles) {
    const data = [];
    let time = new Date(Date.UTC(2023, 0, 1, 0, 0, 0, 0));
    let price = 100;
    
    for (let i = 0; i < numCandles; i++) {
        // Create a random price movement
        let open, high, low, close;
        let range = price * 0.02;
        
        if (trend === 'bullish') {
            // For bullish trend, generally rising with some volatility
            let trendFactor = 1 + (i / numCandles) * 0.2; // Gradual uptrend
            let dailyChange = ((Math.random() - 0.3) * range) * trendFactor;
            
            // Create a flag pattern in the middle
            if (i > numCandles * 0.6 && i < numCandles * 0.8) {
                dailyChange = ((Math.random() - 0.6) * range); // Slight pullback
            }
            
            // Final breakout
            if (i >= numCandles * 0.8) {
                dailyChange = ((Math.random() + 0.3) * range) * trendFactor;
            }
            
            open = price;
            close = price + dailyChange;
            high = Math.max(open, close) + Math.random() * range * 0.5;
            low = Math.min(open, close) - Math.random() * range * 0.5;
        } else {
            // For bearish trend, generally falling with some volatility
            let trendFactor = 1 + (i / numCandles) * 0.2; // Gradual downtrend
            let dailyChange = ((Math.random() - 0.7) * range) * trendFactor;
            
            // Create a double top pattern
            if (i === Math.floor(numCandles * 0.4) || i === Math.floor(numCandles * 0.7)) {
                dailyChange = ((Math.random() + 0.5) * range); // Spike up
            }
            
            // Final breakdown
            if (i >= numCandles * 0.8) {
                dailyChange = ((Math.random() - 0.8) * range) * trendFactor;
            }
            
            open = price;
            close = price + dailyChange;
            high = Math.max(open, close) + Math.random() * range * 0.5;
            low = Math.min(open, close) - Math.random() * range * 0.5;
        }
        
        // Add candle to data
        data.push({
            time: time.getTime() / 1000,
            open: open,
            high: high,
            low: low,
            close: close,
            volume: Math.floor(Math.random() * 1000000)
        });
        
        // Update price for next candle
        price = close;
        
        // Increment time (1 day)
        time.setDate(time.getDate() + 1);
    }
    
    return data;
}

/**
 * Format volume data for mini charts
 */
function formatVolumeData(candleData) {
    if (!candleData || !candleData.length) {
        return [];
    }
    
    // Find the maximum volume
    const maxVolume = Math.max(...candleData.map(item => item.volume));
    
    // Use a small scale factor for better visualization
    const scaleFactor = 0.02 / maxVolume;
    
    return candleData.map(item => {
        const isUpCandle = item.close >= item.open;
        
        // Scale the volume
        const scaledVolume = item.volume * scaleFactor;
        
        return {
            time: item.time,
            value: scaledVolume,
            color: isUpCandle ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)'
        };
    });
}

/**
 * Setup event listeners for the feed page
 */
function setupEventListeners() {
    // Market overview toggle
    const toggleButton = document.querySelector('.toggle-market-detail');
    const detailView = document.querySelector('.market-detail-view');
    
    if (toggleButton && detailView) {
        toggleButton.addEventListener('click', function() {
            // Toggle active class on button
            this.classList.toggle('active');
            
            // Toggle active class on detail view
            detailView.classList.toggle('active');
            
            // Update icon
            const icon = this.querySelector('i');
            if (detailView.classList.contains('active')) {
                icon.classList.replace('fa-chevron-down', 'fa-chevron-up');
            } else {
                icon.classList.replace('fa-chevron-up', 'fa-chevron-down');
            }
        });
    }

    // Apply setup detail click handlers to static setup cards in the HTML
    const existingSetupCards = document.querySelectorAll('.setup-card');
    existingSetupCards.forEach((card, index) => {
        // Assign a setup ID if it doesn't have one
        if (!card.getAttribute('data-setup-id')) {
            const setupId = 1000 + index;
            card.setAttribute('data-setup-id', setupId);
        }
        
        // Add click event listener
        card.addEventListener('click', function(e) {
            // Don't trigger detail view if clicking on action buttons
            if (!e.target.closest('.setup-actions')) {
                const setupId = this.getAttribute('data-setup-id');
                console.log('Clicked on setup card:', setupId);
                
                // Call the showSetupDetail function 
                if (typeof showSetupDetail === 'function') {
                    showSetupDetail(setupId);
                } else if (window.setupDetail && typeof window.setupDetail.showSetupDetail === 'function') {
                    window.setupDetail.showSetupDetail(setupId);
                } else {
                    console.error('showSetupDetail function not found');
                }
            }
        });
    });
    
    // Setup action buttons
    setupActionButtons();
    
    // Setup "Load More" button
    const loadMoreButton = document.querySelector('.setup-feed button.btn-outline');
    if (loadMoreButton) {
        loadMoreButton.addEventListener('click', loadMoreSetups);
    }
    
    // Setup filters
    const filterSelects = document.querySelectorAll('.setup-filters select');
    filterSelects.forEach(select => {
        select.addEventListener('change', filterSetups);
    });
    
    // Window resize handler for responsive charts
    window.addEventListener('resize', () => {
        // Add a small delay to ensure DOM updates are complete
        setTimeout(() => {
            const chartElements = document.querySelectorAll('.setup-mini-chart');
            chartElements.forEach(element => {
                const chart = element.chart;
                if (chart) {
                    chart.applyOptions({
                        width: element.clientWidth,
                        height: element.clientHeight
                    });
                }
            });
        }, 100);
    });
}

/**
 * Show notes popup for a setup
 */
function showNotesPopup(card) {
    // Create modal for notes
    const modal = document.createElement('div');
    modal.className = 'notes-modal';
    modal.innerHTML = `
        <div class="notes-modal-content">
            <div class="notes-modal-header">
                <h3>Trade Notes</h3>
                <button class="close-btn">&times;</button>
            </div>
            <div class="notes-modal-body">
                <textarea placeholder="Add your trading notes here..."></textarea>
            </div>
            <div class="notes-modal-footer">
                <button class="btn-outline">Save Notes</button>
            </div>
        </div>
    `;
    
    // Add to body
    document.body.appendChild(modal);
    
    // Add event listeners
    const closeBtn = modal.querySelector('.close-btn');
    closeBtn.addEventListener('click', function() {
        document.body.removeChild(modal);
    });
    
    const saveBtn = modal.querySelector('.btn-outline');
    saveBtn.addEventListener('click', function() {
        const notes = modal.querySelector('textarea').value;
        if (notes.trim() !== '') {
            // Save notes (in real app, would save to backend)
            console.log('Notes saved:', notes);
            
            // Update button to show notes were added
            const notesBtn = card.querySelector('.setup-action-btn:nth-child(4)');
            notesBtn.innerHTML = '<i class="fas fa-comment-alt"></i> Notes (1)';
            notesBtn.style.color = '#26a69a';
        }
        
        // Close modal
        document.body.removeChild(modal);
    });
}

/**
 * Fetch setups from the server
 */
function fetchSetups() {
    console.log('Fetching sweep engulfing confirmed patterns...');
    
    // Show loading state for the feed
    const setupFeed = document.getElementById('setupFeed');
    if (setupFeed) {
        setupFeed.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Loading setups...</div>';
    }
    
    // Fetch sweep engulfing confirmed patterns from the API
    fetch('/api/setups?setup_type=sweep_engulfing_confirmed')
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Received setup data:', data);
            console.log('Data type:', typeof data);
            console.log('Data length:', Array.isArray(data) ? data.length : 'Not an array');
            
            // Update scan info with real data
            const scanInfo = document.querySelector('.scan-info p');
            if (scanInfo) {
                const now = new Date();
                const timeStr = now.toLocaleTimeString();
                const setupCount = Array.isArray(data) ? data.length : 0;
                scanInfo.innerHTML = `Last scan: <strong>Today, ${timeStr}</strong> • Found <strong>${setupCount}</strong> new setups`;
            }
            
            if (setupFeed) {
                // Clear the loading indicator
                setupFeed.innerHTML = '';
                
                if (!Array.isArray(data) || data.length === 0) {
                    // Show message if no setups found
                    setupFeed.innerHTML = '<div class="no-setups-message">No sweep engulfing patterns detected yet. Check back later.</div>';
                } else {
                    // Create cards for each setup
                    data.forEach(setup => {
                        console.log('Processing setup:', setup);
                        try {
                            const card = createSetupCard(setup);
                            setupFeed.appendChild(card);
                        } catch (error) {
                            console.error('Error creating setup card:', error, setup);
                        }
                    });
                    
                    // Initialize TradingView charts for the cards
                    initTradingViewCharts();
                    
                    // Initialize mini charts
                    try {
                        initMiniCharts();
                    } catch (error) {
                        console.error('Error initializing mini charts:', error);
                    }
                    
                    // Setup action buttons
                    try {
                        setupActionButtons();
                    } catch (error) {
                        console.error('Error setting up action buttons:', error);
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error fetching setups:', error);
            if (setupFeed) {
                setupFeed.innerHTML = '<div class="error-message">Failed to load setups. Please try again.</div>';
            }
        });
}

/**
 * Create a setup card from API data
 */
function createSetupCard(setup) {
    const chartId = 'miniChart' + Math.floor(Math.random() * 10000);
    
    // Handle potential missing or malformed data
    const setupId = setup.id || Math.floor(Math.random() * 10000);
    const symbol = setup.symbol || 'UNKNOWN';
    const timeframe = setup.timeframe || '1D';
    const direction = (setup.direction || '').toLowerCase();
    const isBullish = direction.includes('bull');
    
    // Format prices with fallbacks
    const entryPrice = parseFloat(setup.entry_price) || 0;
    const stopLoss = parseFloat(setup.stop_loss) || 0;
    const target = parseFloat(setup.target) || 0;
    
    // Safely calculate risk/reward ratio
    let riskReward = 0;
    try {
        if (stopLoss !== entryPrice) {
            riskReward = Math.abs(target - entryPrice) / Math.abs(stopLoss - entryPrice);
        }
    } catch (error) {
        console.error('Error calculating R:R ratio:', error);
    }
    
    // Format timestamp
    let timestamp = 'Recently';
    try {
        if (setup.date_identified) {
            const date = new Date(setup.date_identified);
            timestamp = date.toLocaleString();
        } else if (setup.timestamp) {
            const date = new Date(setup.timestamp);
            timestamp = date.toLocaleString();
        }
    } catch (error) {
        console.error('Error formatting timestamp:', error);
    }
    
    const card = document.createElement('div');
    card.className = 'setup-card';
    card.setAttribute('data-setup-id', setupId);
    
    // Store the full setup data as a JSON string in a data attribute
    card.setAttribute('data-setup', JSON.stringify(setup));
    
    card.innerHTML = `
        <div class="setup-header">
            <span class="setup-symbol">${symbol}</span>
            <span class="setup-timeframe">${timeframe}</span>
        </div>
        <div class="setup-meta">
            <span class="setup-type">SWEEP ENGULFING CONFIRMED</span>
            <span class="setup-direction ${isBullish ? 'bullish' : 'bearish'}">
                <i class="fas fa-arrow-${isBullish ? 'up' : 'down'}"></i> ${isBullish ? 'Bullish' : 'Bearish'}
            </span>
        </div>
        <div class="setup-timestamp">
            <i class="far fa-clock"></i> Detected ${timestamp}
        </div>
        <div class="setup-mini-chart" id="${chartId}"></div>
        <div class="setup-metrics">
            <div class="setup-metric">
                <div class="metric-label">Entry</div>
                <div class="metric-value">$${entryPrice.toFixed(2)}</div>
            </div>
            <div class="setup-metric">
                <div class="metric-label">Target</div>
                <div class="metric-value">$${target.toFixed(2)}</div>
            </div>
            <div class="setup-metric">
                <div class="metric-label">Stop Loss</div>
                <div class="metric-value">$${stopLoss.toFixed(2)}</div>
            </div>
            <div class="setup-metric">
                <div class="metric-label">R:R</div>
                <div class="metric-value">${riskReward.toFixed(2)}x</div>
            </div>
        </div>
        <div class="setup-actions">
            <button class="setup-action-btn save-btn">
                <i class="far fa-bookmark"></i> Save
            </button>
            <button class="setup-action-btn alert-btn">
                <i class="far fa-bell"></i> Alert
            </button>
            <button class="setup-action-btn tradingview-btn">
                <i class="fas fa-external-link-alt"></i> Chart
            </button>
            <button class="setup-action-btn notes-btn">
                <i class="far fa-comment-alt"></i> Notes
            </button>
        </div>
    `;
    
    // Add click event to show setup detail
    card.addEventListener('click', function(e) {
        // Don't trigger detail view if clicking on action buttons
        if (!e.target.closest('.setup-actions')) {
            const setupData = JSON.parse(this.getAttribute('data-setup'));
            showSetupDetail(setupId, setupData);
        }
    });
    
    return card;
}

/**
 * Fetch more setups (pagination)
 */
function fetchMoreSetups() {
    console.log('Fetching more sweep engulfing confirmed patterns...');
    
    // Show loading in the load more button
    const loadMoreBtn = document.querySelector('.load-more-btn');
    if (loadMoreBtn) {
        loadMoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        loadMoreBtn.disabled = true;
    }
    
    // Get the current number of setups to use as offset
    const setupFeed = document.getElementById('setupFeed');
    const currentCount = setupFeed ? setupFeed.querySelectorAll('.setup-card').length : 0;
    
    // Fetch more sweep engulfing confirmed patterns from the API with offset
    fetch(`/api/setups?setup_type=sweep_engulfing_confirmed&offset=${currentCount}&limit=5`)
        .then(response => response.json())
        .then(data => {
            console.log('Received more setup data:', data);
            
            // Reset the load more button
            if (loadMoreBtn) {
                loadMoreBtn.innerHTML = 'Load More';
                loadMoreBtn.disabled = false;
            }
            
            if (setupFeed) {
                if (data.length === 0) {
                    // No more setups to load
                    if (loadMoreBtn) {
                        loadMoreBtn.innerHTML = 'No More Setups';
                        loadMoreBtn.disabled = true;
                    }
                } else {
                    // Add new cards to the feed
                    data.forEach(setup => {
                        const card = createSetupCard(setup);
                        setupFeed.appendChild(card);
                    });
                    
                    // Initialize mini charts for new cards
                    initMiniCharts();
                    
                    // Setup action buttons for new cards
                    setupActionButtons();
                }
            }
        })
        .catch(error => {
            console.error('Error fetching more setups:', error);
            
            // Reset the load more button
            if (loadMoreBtn) {
                loadMoreBtn.innerHTML = 'Load More';
                loadMoreBtn.disabled = false;
            }
        });
}

/**
 * Create a sample card for the feed
 */
function createSampleCard(symbol, timeframe, direction, pattern, time) {
    const chartId = 'miniChart' + Math.floor(Math.random() * 10000);
    const isBullish = direction === 'Bullish';
    const setupId = Math.floor(Math.random() * 10000); // Generate a random ID for demo purposes
    
    const card = document.createElement('div');
    card.className = 'setup-card';
    card.setAttribute('data-setup-id', setupId);
    card.innerHTML = `
        <div class="setup-header">
            <span class="setup-symbol">${symbol}</span>
            <span class="setup-timeframe">${timeframe}</span>
        </div>
        <div class="setup-meta">
            <span class="setup-type">${pattern}</span>
            <span class="setup-direction ${isBullish ? 'bullish' : 'bearish'}">
                <i class="fas fa-arrow-${isBullish ? 'up' : 'down'}"></i> ${direction}
            </span>
        </div>
        <div class="setup-timestamp">
            <i class="far fa-clock"></i> Detected ${time}
        </div>
        <div class="setup-mini-chart" id="${chartId}"></div>
        <div class="setup-metrics">
            <div class="setup-metric">
                <div class="metric-label">Entry</div>
                <div class="metric-value">$${Math.floor(Math.random() * 500 + 100)}.${Math.floor(Math.random() * 100)}</div>
            </div>
            <div class="setup-metric">
                <div class="metric-label">Target</div>
                <div class="metric-value">$${Math.floor(Math.random() * 500 + 100)}.${Math.floor(Math.random() * 100)}</div>
            </div>
            <div class="setup-metric">
                <div class="metric-label">Stop Loss</div>
                <div class="metric-value">$${Math.floor(Math.random() * 500 + 100)}.${Math.floor(Math.random() * 100)}</div>
            </div>
        </div>
        <div class="setup-actions">
            <button class="setup-action-btn">
                <i class="far fa-bookmark"></i> Save
            </button>
            <button class="setup-action-btn">
                <i class="far fa-bell"></i> Alert
            </button>
            <button class="setup-action-btn">
                <i class="fas fa-external-link-alt"></i> TradingView
            </button>
            <button class="setup-action-btn">
                <i class="far fa-comment-alt"></i> Notes
            </button>
        </div>
    `;
    
    // Add click event to show setup detail
    card.addEventListener('click', function(e) {
        // Don't trigger detail view if clicking on action buttons
        if (!e.target.closest('.setup-actions')) {
            showSetupDetail(setupId);
        }
    });
    
    return card;
}

/**
 * Filter setups based on dropdown selections
 */
function filterSetups() {
    const setupTypeFilter = document.querySelector('.setup-filters select:nth-child(1)').value;
    const timeframeFilter = document.querySelector('.setup-filters select:nth-child(2)').value;
    
    console.log(`Filtering setups: ${setupTypeFilter}, ${timeframeFilter}`);
    
    // In a real app, this would filter the existing setups or fetch filtered setups
    const setupCards = document.querySelectorAll('.setup-card');
    
    setupCards.forEach(card => {
        let showCard = true;
        
        // Filter by setup type
        if (setupTypeFilter !== 'all') {
            const setupType = card.querySelector('.setup-type').textContent.toLowerCase();
            if (!setupType.includes(setupTypeFilter.toLowerCase())) {
                showCard = false;
            }
        }
        
        // Filter by timeframe
        if (timeframeFilter !== 'all') {
            const timeframe = card.querySelector('.setup-timeframe').textContent.toLowerCase();
            if (!timeframe.toLowerCase().includes(timeframeFilter.toLowerCase())) {
                showCard = false;
            }
        }
        
        // Show or hide card
        card.style.display = showCard ? 'block' : 'none';
    });
}

/**
 * Add EMA to chart
 */
function addEMA(chart, data, period, color) {
    // Calculate EMA
    const closes = data.map(d => d.close);
    const emaValues = calculateEMA(closes, period);
    
    // Create line series for EMA
    const emaSeries = chart.addLineSeries({
        color: color,
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
    });
    
    // Set EMA data
    const emaData = [];
    for (let i = 0; i < emaValues.length; i++) {
        const index = i + period - 1;
        if (index < data.length) {
            emaData.push({
                time: data[index].time,
                value: emaValues[i]
            });
        }
    }
    
    emaSeries.setData(emaData);
}

/**
 * Calculate EMA values
 */
function calculateEMA(prices, period) {
    const results = [];
    const k = 2 / (period + 1);
    
    // Calculate SMA for the first data point
    let sma = 0;
    for (let i = 0; i < period; i++) {
        sma += prices[i];
    }
    sma /= period;
    
    // Use SMA as the first EMA
    results.push(sma);
    
    // Calculate EMA for the rest
    for (let i = period; i < prices.length; i++) {
        const ema = prices[i] * k + results[results.length - 1] * (1 - k);
        results.push(ema);
    }
    
    return results;
}

/**
 * Add SMA to chart
 */
function addSMA(chart, data, period, color) {
    // Calculate SMA
    const closes = data.map(d => d.close);
    const smaValues = calculateSMA(closes, period);
    
    // Create line series for SMA
    const smaSeries = chart.addLineSeries({
        color: color,
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: false,
    });
    
    // Set SMA data
    const smaData = [];
    for (let i = 0; i < smaValues.length; i++) {
        const index = i + period - 1;
        if (index < data.length) {
            smaData.push({
                time: data[index].time,
                value: smaValues[i]
            });
        }
    }
    
    smaSeries.setData(smaData);
}

/**
 * Calculate SMA values
 */
function calculateSMA(prices, period) {
    const results = [];
    
    for (let i = 0; i <= prices.length - period; i++) {
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += prices[i + j];
        }
        results.push(sum / period);
    }
    
    return results;
}

/**
 * Setup action buttons for all setup cards
 */
function setupActionButtons() {
    const setupCards = document.querySelectorAll('.setup-card');
    setupCards.forEach(card => {
        // Save button
        const saveBtn = card.querySelector('.setup-action-btn:nth-child(1)');
        if (saveBtn) {
            saveBtn.addEventListener('click', function() {
                this.innerHTML = '<i class="fas fa-bookmark"></i> Saved';
                this.style.color = '#26a69a';
            });
        }
        
        // Alert button
        const alertBtn = card.querySelector('.setup-action-btn:nth-child(2)');
        if (alertBtn) {
            alertBtn.addEventListener('click', function() {
                this.innerHTML = '<i class="fas fa-bell"></i> Alerted';
                this.style.color = '#26a69a';
            });
        }
        
        // TradingView button
        const tvBtn = card.querySelector('.setup-action-btn:nth-child(3)');
        if (tvBtn) {
            tvBtn.addEventListener('click', function() {
                const symbol = card.querySelector('.setup-symbol').textContent;
                window.open(`https://www.tradingview.com/chart/?symbol=${symbol}`, '_blank');
            });
        }
        
        // Notes button
        const notesBtn = card.querySelector('.setup-action-btn:nth-child(4)');
        if (notesBtn) {
            notesBtn.addEventListener('click', function() {
                showNotesPopup(card);
            });
        }
    });
}

/**
 * Load more setups when the load more button is clicked
 */
function loadMoreSetups() {
    const loadMoreBtn = document.querySelector('.setup-feed > .btn-outline');
    if (loadMoreBtn) {
        loadMoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        setTimeout(() => {
            fetchMoreSetups();
            loadMoreBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Load More Setups';
        }, 1000);
    }
}

/**
 * Initialize TradingView charts for each setup card
 */
function initTradingViewCharts() {
    // Get all mini chart containers
    const chartContainers = document.querySelectorAll('.setup-mini-chart');
    
    console.log(`Initializing ${chartContainers.length} TradingView charts for setup cards`);
    
    chartContainers.forEach(container => {
        const chartId = container.id;
        const card = container.closest('.setup-card');
        if (!card) return;
        
        const setupId = card.getAttribute('data-setup-id');
        const symbol = card.querySelector('.setup-symbol')?.textContent || 'AAPL';
        const direction = card.querySelector('.setup-direction')?.classList.contains('bullish') ? 'bullish' : 'bearish';
        
        console.log(`Creating chart for ${symbol}, id: ${chartId}, direction: ${direction}`);
        
        try {
            // Create a lightweight chart
            const chart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: 225,
                layout: {
                    background: { color: '#1E222D' },
                    textColor: '#d1d4dc',
                    fontSize: 12,
                    fontFamily: 'Inter, sans-serif',
                },
                grid: {
                    vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
                    horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
                },
                rightPriceScale: {
                    borderColor: 'rgba(197, 203, 206, 0.4)',
                    visible: true,
                },
                timeScale: {
                    borderColor: 'rgba(197, 203, 206, 0.4)',
                    timeVisible: true,
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
            });
            
            // Store chart reference
            container.chart = chart;
            
            // Generate sample data based on direction
            const sampleData = createSampleData(direction, 30);
            
            // Add candlestick series
            const candlestickSeries = chart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });
            
            // Set data
            candlestickSeries.setData(sampleData);
            
            // Add volume series
            const volumeSeries = chart.addHistogramSeries({
                color: '#26a69a',
                priceFormat: {
                    type: 'volume',
                },
                priceScaleId: 'volume',
                scaleMargins: {
                    top: 0.8,
                    bottom: 0,
                },
            });
            
            // Set volume data
            volumeSeries.setData(formatVolumeData(sampleData));
            
            // Hide the volume price scale
            chart.priceScale('volume').applyOptions({
                scaleMargins: {
                    top: 0.8,
                    bottom: 0,
                },
                visible: false,
            });
            
            // Add indicator appropriate for the pattern type
            if (direction === 'bullish') {
                addEMA(chart, sampleData, 20, '#2962FF');
            } else {
                addSMA(chart, sampleData, 50, '#FF9800');
            }
            
            // Add entry marker
            const lastIndex = sampleData.length - 1;
            const entryPoint = sampleData[lastIndex - 5];
            
            const markerSeries = chart.addLineSeries({
                lastValueVisible: false,
                priceLineVisible: false,
            });
            
            markerSeries.setMarkers([
                {
                    time: entryPoint.time,
                    position: direction === 'bullish' ? 'aboveBar' : 'belowBar',
                    color: direction === 'bullish' ? '#26a69a' : '#ef5350',
                    shape: direction === 'bullish' ? 'arrowUp' : 'arrowDown',
                    text: 'Entry',
                    size: 2
                }
            ]);
            
            console.log(`Successfully created chart for ${symbol}`);
            
        } catch (error) {
            console.error(`Error creating chart for ${symbol}:`, error);
            container.innerHTML = `<div class="chart-error">Chart unavailable</div>`;
        }
    });
}