/**
 * Trade Hub - TradingView Lightweight Charts Integration
 * This file handles the initialization and management of TradingView charts for financial visualization
 */

// Global chart instances
let mainChartContainer = null;
let orderFlowChartContainer = null;
let mainChart = null;
let candleSeries = null;
let volumeSeries = null;
let orderFlowChart = null;
let orderFlowSeries = null;
let currentSymbol = 'AAPL';
let currentTimeframe = '1D';

// WebSocket connection
let socket = null;
let socketConnected = false;
let isSubscribed = false;

// Store active indicators
let activeIndicators = [];

// Drawing tools state
let drawingToolState = {
    activeTool: 'cursor',
    lines: [],
    rectangles: [],
    fibonacciLevels: [],
    textNotes: [],
    activeDrawing: null,
    isDrawing: false,
    startPoint: null
};

// Initialize charts on document load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize main price chart
    initMainChart();
    
    // Initialize order flow chart
    initOrderFlowChart();
    
    // Set up event listeners
    setupEventListeners();
    
    // Connect to WebSocket for real-time updates
    connectWebSocket();
    
    // Load initial data
    loadSymbolData(currentSymbol, currentTimeframe);
    
    // Load setups
    loadSetups();
    
    // Setup drawing tools
    setupDrawingTools();
});

/**
 * Connect to WebSocket for real-time data updates
 */
function connectWebSocket() {
    try {
        console.log('Connecting to WebSocket...');
        
        // Check if the Socket.io library is available
        if (typeof io === 'undefined') {
            console.error('Socket.io is not loaded. Real-time updates will not be available.');
            return;
        }
        
        // Create WebSocket connection
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${window.location.protocol}//${window.location.host}`;
        
        socket = io(wsUrl);
        
        // Set up event handlers
        socket.on('connect', () => {
            console.log('WebSocket connected');
            socketConnected = true;
            
            // Subscribe to current symbol
            subscribeToSymbol(currentSymbol);
        });
        
        socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            socketConnected = false;
            isSubscribed = false;
        });
        
        socket.on('price_update', (data) => {
            console.log('Received price update:', data);
            
            // Update the candlestick chart with the new data
            if (candleSeries && data.symbol === currentSymbol) {
                const formattedData = {
                    time: new Date(data.date).getTime() / 1000,
                    open: data.open,
                    high: data.high,
                    low: data.low,
                    close: data.close
                };
                
                candleSeries.update(formattedData);
                
                // Update volume
                if (volumeSeries) {
                    const volumeData = {
                        time: formattedData.time,
                        value: data.volume,
                        color: data.close >= data.open ? '#26a69a' : '#ef5350'
                    };
                    volumeSeries.update(volumeData);
                }
                
                // Update last price display
                updateLastPrice(data.close);
            }
        });
        
        socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            socketConnected = false;
        });
        
    } catch (error) {
        console.error('Error connecting to WebSocket:', error);
    }
}

/**
 * Subscribe to real-time updates for a symbol
 */
function subscribeToSymbol(symbol) {
    if (!socketConnected || !socket) {
        console.warn('WebSocket not connected. Cannot subscribe to symbol.');
        return;
    }
    
    console.log(`Subscribing to real-time updates for ${symbol}...`);
    
    // Unsubscribe from previous symbol if different
    if (isSubscribed && symbol !== currentSymbol) {
        socket.emit('unsubscribe', { symbol: currentSymbol });
    }
    
    // Subscribe to new symbol
    socket.emit('subscribe', { symbol: symbol }, (response) => {
        if (response && response.status === 'success') {
            console.log(`Successfully subscribed to ${symbol}`);
            isSubscribed = true;
        } else {
            console.error(`Failed to subscribe to ${symbol}:`, response ? response.message : 'Unknown error');
            isSubscribed = false;
        }
    });
}

/**
 * Update the last price display
 */
function updateLastPrice(price) {
    const lastPriceElement = document.getElementById('lastPrice');
    if (lastPriceElement) {
        lastPriceElement.textContent = `${price.toFixed(2)}`;
    }
}

/**
 * Initialize the main price chart
 */
function initMainChart() {
    try {
        const chartContainer = document.getElementById('mainChart');
        if (!chartContainer) {
            console.error('Chart container not found');
            return;
        }
        
        // Create chart
        mainChart = LightweightCharts.createChart(chartContainer, {
            layout: {
                background: { color: '#1E222D' },
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
                horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    width: 1,
                    color: 'rgba(224, 227, 235, 0.1)',
                    style: LightweightCharts.LineStyle.Dotted,
                },
                horzLine: {
                    width: 1,
                    color: 'rgba(224, 227, 235, 0.1)',
                    style: LightweightCharts.LineStyle.Dotted,
                },
            },
            rightPriceScale: {
                borderColor: 'rgba(197, 203, 206, 0.8)',
                visible: true,
                scaleMargins: {
                    top: 0.1,  
                    bottom: 0.2  // Leave space for volume
                }
            },
            timeScale: {
                borderColor: 'rgba(197, 203, 206, 0.8)',
                timeVisible: true,
                secondsVisible: false,
            },
            handleScroll: {
                vertTouchDrag: true,
            },
            handleScale: {
                axisPressedMouseMove: {
                    time: true,
                    price: true,
                },
                mouseWheel: true,
                pinch: true,
            },
            // Enable kinetic scrolling
            kineticScroll: {
                touch: true,
                mouse: true,
            }
        });
        
        // Add candlestick series
        candleSeries = mainChart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
            priceScaleId: 'right'
        });
        
        // Add volume series
        volumeSeries = mainChart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: 'volume', // Use a separate scale for volume
            scaleMargins: {
                top: 0.8, // Positions the volume at the bottom 20% of the chart
                bottom: 0
            },
        });
        
        // Set scale options for volume
        mainChart.priceScale('volume').applyOptions({
            scaleMargins: {
                top: 0.8,
                bottom: 0
            },
            visible: false // Hide the price scale for volume
        });
        
        // Allow chart to be zoomed and panned
        mainChart.timeScale().fitContent();
        
        // Add a tool tip (legend)
        const toolTipWidth = 96;
        const toolTipHeight = 80;
        const toolTipMargin = 15;
        
        const toolTip = document.createElement('div');
        toolTip.className = 'chart-tooltip';
        toolTip.style.display = 'none';
        chartContainer.appendChild(toolTip);
        
        // Add crosshair legend
        mainChart.subscribeCrosshairMove((param) => {
            if (!param || !param.time || param.point === undefined || 
                !param.point.x || !param.point.y || !param.seriesData || 
                param.seriesData.size === 0) {
                toolTip.style.display = 'none';
                return;
            }
            
            const data = param.seriesData.get(candleSeries);
            if (!data) {
                toolTip.style.display = 'none';
                return;
            }
            
            toolTip.style.display = 'block';
            
            const dateStr = new Date(param.time * 1000).toLocaleDateString();
            toolTip.innerHTML = `
                <div class="tooltip-date">${dateStr}</div>
                <div class="tooltip-price">
                    <div>O: <span class="tooltip-value">${data.open.toFixed(2)}</span></div>
                    <div>H: <span class="tooltip-value">${data.high.toFixed(2)}</span></div>
                    <div>L: <span class="tooltip-value">${data.low.toFixed(2)}</span></div>
                    <div>C: <span class="tooltip-value">${data.close.toFixed(2)}</span></div>
                </div>
            `;
            
            // Position the tooltip
            const y = param.point.y;
            const x = param.point.x;
            
            let left = x + toolTipMargin;
            if (left > chartContainer.clientWidth - toolTipWidth) {
                left = x - toolTipMargin - toolTipWidth;
            }
            
            let top = y + toolTipMargin;
            if (top > chartContainer.clientHeight - toolTipHeight) {
                top = y - toolTipHeight - toolTipMargin;
            }
            
            toolTip.style.left = left + 'px';
            toolTip.style.top = top + 'px';
        });
        
        // Subscribe to clicks for drawing tools
        mainChart.subscribeClick((param) => {
            console.log('Chart clicked:', param);
            // Will be used for drawing tools
        });
        
        // Load initial symbol data
        loadSymbolData(currentSymbol, currentTimeframe);
        
        console.log('Main chart initialized');
    } catch (error) {
        console.error('Error initializing main chart:', error);
    }
}

/**
 * Initialize the order flow chart with TradingView Lightweight Charts
 */
function initOrderFlowChart() {
    orderFlowChartContainer = document.getElementById('orderFlowChart');
    
    if (!orderFlowChartContainer) {
        console.error('Order flow chart container not found');
        return;
    }
    
    console.log('Initializing order flow chart...');
    
    try {
        // Create chart
        orderFlowChart = LightweightCharts.createChart(orderFlowChartContainer, {
            width: orderFlowChartContainer.clientWidth,
            height: orderFlowChartContainer.clientHeight,
            layout: {
                background: { color: '#1E222D' },
                textColor: '#D1D4DC',
            },
            grid: {
                vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
                horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderColor: '#363A45',
            },
        });
        
        console.log('Order flow chart created, adding series...');
        
        // Create histogram series for order flow
        orderFlowSeries = orderFlowChart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
        });
        
        console.log('Order flow series added');
        
        // Handle window resize
        window.addEventListener('resize', () => {
            if (orderFlowChart) {
                orderFlowChart.applyOptions({
                    width: orderFlowChartContainer.clientWidth,
                    height: orderFlowChartContainer.clientHeight
                });
            }
        });
    } catch (error) {
        console.error('Error initializing order flow chart:', error);
    }
}

/**
 * Set up event listeners for chart controls
 */
function setupEventListeners() {
    // Symbol select
    const symbolSelect = document.getElementById('symbolSelect');
    if (symbolSelect) {
        symbolSelect.addEventListener('change', (e) => {
            currentSymbol = e.target.value;
            loadSymbolData(currentSymbol, currentTimeframe);
        });
    }
    
    // Timeframe buttons
    const timeframeButtons = document.querySelectorAll('.timeframe-btn');
    timeframeButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            timeframeButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
            
            // Update timeframe and load data
            currentTimeframe = button.dataset.timeframe;
            loadSymbolData(currentSymbol, currentTimeframe);
        });
    });
    
    // Add Indicator button
    const addIndicatorBtn = document.getElementById('addIndicator');
    if (addIndicatorBtn) {
        addIndicatorBtn.addEventListener('click', () => {
            // Create a dropdown/popup for indicator selection
            showIndicatorMenu();
        });
    }
    
    // Chatbot suggestion buttons
    const suggestionBtns = document.querySelectorAll('.suggestion-btn');
    suggestionBtns.forEach(button => {
        button.addEventListener('click', () => {
            const text = button.textContent.trim();
            
            if (text.includes('EMA')) {
                const period = parseInt(text.match(/\d+/)[0]);
                addEMA(period, '#2962FF');
            } else if (text.includes('high/low')) {
                addDailyHighLow();
            } else if (text.includes('fair value gaps')) {
                findFairValueGaps();
            }
        });
    });
    
    // Symbol search input
    const symbolSearch = document.getElementById('symbolSearch');
    if (symbolSearch) {
        symbolSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const symbol = symbolSearch.value.trim().toUpperCase();
                if (symbol) {
                    currentSymbol = symbol;
                    loadSymbolData(currentSymbol, currentTimeframe);
                    updateSymbolInfo(symbol);
                }
            }
        });
    }
    
    // Timeframe selector dropdown
    const timeframeSelector = document.getElementById('timeframeSelector');
    if (timeframeSelector) {
        timeframeSelector.addEventListener('change', () => {
            currentTimeframe = timeframeSelector.value;
            loadSymbolData(currentSymbol, currentTimeframe);
        });
    }
    
    // Chatbot input
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotSendBtn = document.getElementById('chatbotSendBtn');
    
    if (chatbotInput && chatbotSendBtn) {
        const sendChatMessage = () => {
            const message = chatbotInput.value.trim();
            if (message) {
                // Add user message to chat
                addChatMessage(message, 'user');
                
                // Process the message
                processChatbotCommand(message);
                
                // Clear input
                chatbotInput.value = '';
            }
        };
        
        chatbotInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
        
        chatbotSendBtn.addEventListener('click', sendChatMessage);
    }
}

/**
 * Show indicator menu
 */
function showIndicatorMenu() {
    // Create popup menu for indicator selection
    const menu = document.createElement('div');
    menu.className = 'indicator-menu';
    menu.innerHTML = `
        <div class="indicator-menu-header">
            <h3>Add Indicator</h3>
            <button class="close-btn">&times;</button>
        </div>
        <div class="indicator-menu-content">
            <div class="indicator-group">
                <h4>Moving Averages</h4>
                <button data-indicator="ema" data-period="20">EMA 20</button>
                <button data-indicator="ema" data-period="50">EMA 50</button>
                <button data-indicator="sma" data-period="200">SMA 200</button>
            </div>
            <div class="indicator-group">
                <h4>Price Action</h4>
                <button data-indicator="vwap">VWAP</button>
                <button data-indicator="dailyhl">Daily High/Low</button>
            </div>
            <div class="indicator-group">
                <h4>Custom</h4>
                <div class="custom-indicator">
                    <select id="indicatorType">
                        <option value="ema">EMA</option>
                        <option value="sma">SMA</option>
                    </select>
                    <input type="number" id="indicatorPeriod" placeholder="Period" min="1" value="20">
                    <button id="addCustomIndicator">Add</button>
                </div>
            </div>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(menu);
    
    // Add event listeners
    const closeBtn = menu.querySelector('.close-btn');
    closeBtn.addEventListener('click', () => {
        document.body.removeChild(menu);
    });
    
    // Indicator buttons
    const indicatorBtns = menu.querySelectorAll('[data-indicator]');
    indicatorBtns.forEach(button => {
        button.addEventListener('click', () => {
            const indicator = button.dataset.indicator;
            const period = button.dataset.period ? parseInt(button.dataset.period) : null;
            
            if (indicator === 'ema' && period) {
                addEMA(period, '#2962FF');
            } else if (indicator === 'sma' && period) {
                addSMA(period, '#FF9800');
            } else if (indicator === 'vwap') {
                addVWAP('#9C27B0');
            } else if (indicator === 'dailyhl') {
                addDailyHighLow();
            }
            
            document.body.removeChild(menu);
        });
    });
    
    // Custom indicator button
    const addCustomBtn = menu.querySelector('#addCustomIndicator');
    addCustomBtn.addEventListener('click', () => {
        const type = menu.querySelector('#indicatorType').value;
        const period = parseInt(menu.querySelector('#indicatorPeriod').value);
        
        if (type === 'ema' && period) {
            addEMA(period, '#2962FF');
        } else if (type === 'sma' && period) {
            addSMA(period, '#FF9800');
        }
        
        document.body.removeChild(menu);
    });
}

/**
 * Add chat message to the chatbot
 */
function addChatMessage(message, sender) {
    const chatMessages = document.getElementById('chatbotMessages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    messageDiv.innerHTML = `
        <div class="message-content">
            <p>${message}</p>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Process chatbot command
 */
function processChatbotCommand(message) {
    message = message.toLowerCase();
    
    if (message.includes('ema') || message.includes('moving average')) {
        // Extract the period from the message
        const match = message.match(/\d+/);
        const period = match ? parseInt(match[0]) : 20;
        
        addEMA(period, '#2962FF');
        addChatMessage(`Added EMA ${period} to the chart.`, 'bot');
    } else if (message.includes('sma')) {
        // Extract the period from the message
        const match = message.match(/\d+/);
        const period = match ? parseInt(match[0]) : 50;
        
        addSMA(period, '#FF9800');
        addChatMessage(`Added SMA ${period} to the chart.`, 'bot');
    } else if (message.includes('vwap')) {
        addVWAP('#9C27B0');
        addChatMessage('Added VWAP to the chart.', 'bot');
    } else if (message.includes('high') && message.includes('low')) {
        addDailyHighLow();
        addChatMessage('Added daily high and low levels to the chart.', 'bot');
    } else {
        // Default response
        addChatMessage('I\'m not sure how to help with that. Try asking for indicators like "Add EMA 20" or "Show daily high/low".', 'bot');
    }
}

/**
 * Load symbol data from API
 */
function loadSymbolData(symbol, timeframe) {
    try {
        console.log(`Loading data for ${symbol} (${timeframe})...`);
        
        // Update UI
        document.getElementById('currentSymbol').textContent = symbol;
        document.getElementById('currentTimeframe').textContent = getTimeframeText(timeframe);
        
        // Update chart title
        const chartTitle = document.querySelector('.chart-title');
        if (chartTitle) {
            chartTitle.textContent = `${symbol} - ${getTimeframeText(timeframe)}`;
        }
        
        // Subscribe to real-time updates for this symbol
        if (socketConnected && socket) {
            subscribeToSymbol(symbol);
        }
        
        // Convert timeframe to API format
        const apiTimeframe = timeframe.toLowerCase();
        
        // Fetch data from API
        fetch(`/api/price-data/${symbol}?timeframe=${apiTimeframe}`)
            .then(response => response.json())
            .then(data => {
                console.log(`Received ${data.length} data points for ${symbol}`);
                
                // Format and set the data
                const formattedData = formatCandlestickData(data);
                candleSeries.setData(formattedData);
                
                // Set volume data
                const volumeData = formatVolumeData(data);
                volumeSeries.setData(volumeData);
                
                // Fit the visible range
                mainChart.timeScale().fitContent();
                
                // Update symbol information
                updateSymbolInfo(symbol);
                
                // Store current symbol and timeframe
                currentSymbol = symbol;
                currentTimeframe = timeframe;
                
                // Load order flow data if available
                loadOrderFlowData(symbol);
            })
            .catch(error => {
                console.error(`Error loading data for ${symbol}:`, error);
            });
    } catch (error) {
        console.error('Error in loadSymbolData:', error);
    }
}

/**
 * Load order flow data from API
 */
function loadOrderFlowData(symbol) {
    fetch(`/api/analysis/${symbol}`)
        .then(response => response.json())
        .then(data => {
            if (data.order_flow && data.order_flow.data) {
                // Format order flow data for chart
                const orderFlowData = formatOrderFlowData(data.order_flow.data);
                
                // Update order flow chart
                orderFlowSeries.setData(orderFlowData);
            }
        })
        .catch(error => {
            console.error('Error loading order flow data:', error);
        });
}

/**
 * Format candlestick data for TradingView charts
 */
function formatCandlestickData(data) {
    console.log('Formatting candlestick data, sample item:', data[0]);
    return data.map(item => {
        return {
            time: item.time,
            open: parseFloat(item.open),
            high: parseFloat(item.high),
            low: parseFloat(item.low),
            close: parseFloat(item.close)
        };
    });
}

/**
 * Format volume data for TradingView chart
 */
function formatVolumeData(data) {
    try {
        if (!data || !data.length) {
            return [];
        }
        
        // Find the maximum volume for scaling
        let maxVolume = Math.max(...data.map(item => parseFloat(item.volume)));
        
        // Use a much smaller scale factor for better visualization
        // This will make volume bars much smaller - reduced further to 0.02
        const scaleFactor = 0.02 / maxVolume;
        
        return data.map(item => {
            const isUpCandle = parseFloat(item.close) >= parseFloat(item.open);
            
            // Scale the volume to be much smaller proportion of the chart
            const scaledVolume = parseFloat(item.volume) * scaleFactor;
            
            return {
                time: item.time,
                value: scaledVolume,
                color: isUpCandle ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)'
            };
        });
    } catch (error) {
        console.error('Error formatting volume data:', error);
        return [];
    }
}

/**
 * Format order flow data for TradingView charts
 */
function formatOrderFlowData(data) {
    return data.map(item => {
        return {
            time: item.time,
            value: parseFloat(item.value),
            color: parseFloat(item.value) >= 0 
                ? 'rgba(38, 166, 154, 0.5)' 
                : 'rgba(239, 83, 80, 0.5)'
        };
    });
}

/**
 * Load trade setups from the API
 */
function loadSetups() {
    const setupsContainer = document.getElementById('setupsContainer');
    setupsContainer.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i><span>Loading setups...</span></div>';
    
    // Fetch setups from API
    fetch('/api/setups')
        .then(response => response.json())
        .then(data => {
            if (data && data.length) {
                const setupsHTML = data
                    .slice(0, 4) // Show only 4 setups in dashboard
                    .map(setup => createSetupCard(setup))
                    .join('');
                
                setupsContainer.innerHTML = setupsHTML;
                
                // Add click event listeners to setup cards
                document.querySelectorAll('.setup-card').forEach(card => {
                    card.addEventListener('click', () => {
                        const symbol = card.getAttribute('data-symbol');
                        if (symbol) {
                            currentSymbol = symbol;
                            loadSymbolData(symbol, currentTimeframe);
                            updateSymbolInfo(symbol);
                        }
                    });
                });
            } else {
                setupsContainer.innerHTML = '<div class="placeholder-text"><i class="fas fa-info-circle"></i><p>No setups found</p></div>';
            }
        })
        .catch(error => {
            console.error('Error fetching setups:', error);
            setupsContainer.innerHTML = '<div class="placeholder-text"><i class="fas fa-exclamation-circle"></i><p>Error loading setups</p></div>';
        });
}

/**
 * Create a setup card HTML
 */
function createSetupCard(setup) {
    return `
        <div class="setup-card" data-symbol="${setup.symbol}">
            <div class="setup-header">
                <span class="setup-symbol">${setup.symbol}</span>
                <span class="setup-timeframe">${setup.timeframe}</span>
            </div>
            <div class="setup-type">${setup.setup_type}</div>
            <span class="setup-direction ${setup.direction}">${setup.direction}</span>
            <div class="setup-metrics">
                <div class="setup-metric">
                    <span class="metric-label">Entry</span>
                    <span class="metric-value">$${setup.entry_price}</span>
                </div>
                <div class="setup-metric">
                    <span class="metric-label">Stop</span>
                    <span class="metric-value">$${setup.stop_loss}</span>
                </div>
                <div class="setup-metric">
                    <span class="metric-label">Target</span>
                    <span class="metric-value">$${setup.target}</span>
                </div>
                <div class="setup-metric">
                    <span class="metric-label">R:R</span>
                    <span class="metric-value">${setup.risk_reward}</span>
                </div>
            </div>
        </div>
    `;
}

/**
 * Update symbol info in the header
 */
function updateSymbolInfo(symbol) {
    document.getElementById('currentSymbol').textContent = symbol;
}

/**
 * Convert timeframe string to milliseconds
 */
function timeframeToMilliseconds(timeframe) {
    switch (timeframe) {
        case '1min':
            return 60 * 1000;
        case '5min':
            return 5 * 60 * 1000;
        case '15min':
            return 15 * 60 * 1000;
        case '1H':
            return 60 * 60 * 1000;
        case '4H':
            return 4 * 60 * 60 * 1000;
        case '1D':
            return 24 * 60 * 60 * 1000;
        default:
            return 24 * 60 * 60 * 1000;
    }
}

/**
 * Get timeframe text
 */
function getTimeframeText(timeframe) {
    switch (timeframe) {
        case '1min':
            return '1 Minute';
        case '5min':
            return '5 Minutes';
        case '15min':
            return '15 Minutes';
        case '1H':
            return '1 Hour';
        case '4H':
            return '4 Hours';
        case '1D':
            return '1 Day';
        default:
            return '1 Day';
    }
}

/**
 * Add EMA indicator to the chart
 */
function addEMA(period, color = '#2962FF') {
    try {
        // Track loading state
        const indicatorId = `ema-${period}`;
        
        // Check if this indicator is already active
        if (activeIndicators.some(i => i.id === indicatorId)) {
            console.log(`EMA ${period} is already on the chart`);
            return;
        }
        
        // Add indicator badge
        addIndicatorBadge(`EMA ${period}`, color, indicatorId);
        
        // Fetch the most recent data
        fetch(`/api/price-data/${currentSymbol}?timeframe=${currentTimeframe}`)
            .then(response => response.json())
            .then(data => {
                if (!data || !data.length) {
                    console.error('No data available for EMA calculation');
                    return;
                }
                
                // Calculate EMA
                const prices = data.map(item => item.close);
                const emaValues = calculateEMA(prices, period);
                
                // Format data for TradingView
                const emaData = data.slice(period - 1).map((item, index) => ({
                    time: item.time,
                    value: emaValues[index]
                }));
                
                // Create EMA series
                const emaSeries = mainChart.addLineSeries({
                    color: color,
                    lineWidth: 2,
                    priceScaleId: 'right'
                });
                
                emaSeries.setData(emaData);
                
                // Store for later removal
                activeIndicators.push({
                    id: indicatorId,
                    type: 'ema',
                    period: period,
                    series: emaSeries,
                    color: color
                });
                
                // Update chart
                mainChart.applyOptions({
                    watermark: {
                        visible: true,
                        fontSize: 12,
                        horzAlign: 'left',
                        vertAlign: 'bottom',
                        color: 'rgba(255, 255, 255, 0.5)',
                        text: `EMA(${period}): ${emaValues[emaValues.length - 1].toFixed(2)}`
                    }
                });
            })
            .catch(error => {
                console.error('Error adding EMA:', error);
                removeIndicatorBadge(indicatorId);
            });
    } catch (e) {
        console.error('Error in addEMA:', e);
    }
}

/**
 * Calculate EMA values
 * @param {Array} prices - Array of price values
 * @param {number} period - Period for EMA calculation
 * @returns {Array} - EMA values
 */
function calculateEMA(prices, period) {
    const k = 2 / (period + 1);
    let emaValues = [];
    
    // Calculate first EMA as SMA
    let sum = 0;
    for (let i = 0; i < period; i++) {
        sum += prices[i];
    }
    let ema = sum / period;
    emaValues.push(ema);
    
    // Calculate remaining EMAs
    for (let i = period; i < prices.length; i++) {
        ema = (prices[i] * k) + (ema * (1 - k));
        emaValues.push(ema);
    }
    
    // Pad the beginning with null values
    const result = Array(period - 1).fill(null).concat(emaValues);
    return result;
}

/**
 * Add SMA indicator to the chart
 */
function addSMA(period, color = '#FF9800') {
    try {
        // Track loading state
        const indicatorId = `sma-${period}`;
        
        // Check if this indicator is already active
        if (activeIndicators.some(i => i.id === indicatorId)) {
            console.log(`SMA ${period} is already on the chart`);
            return;
        }
        
        // Add indicator badge
        addIndicatorBadge(`SMA ${period}`, color, indicatorId);
        
        // Fetch the most recent data
        fetch(`/api/price-data/${currentSymbol}?timeframe=${currentTimeframe}`)
            .then(response => response.json())
            .then(data => {
                if (!data || !data.length) {
                    console.error('No data available for SMA calculation');
                    return;
                }
                
                // Calculate SMA
                const prices = data.map(item => item.close);
                const smaValues = calculateSMA(prices, period);
                
                // Format data for TradingView
                const smaData = data.slice(period - 1).map((item, index) => ({
                    time: item.time,
                    value: smaValues[index]
                }));
                
                // Create SMA series
                const smaSeries = mainChart.addLineSeries({
                    color: color,
                    lineWidth: 2,
                    priceScaleId: 'right'
                });
                
                smaSeries.setData(smaData);
                
                // Store for later removal
                activeIndicators.push({
                    id: indicatorId,
                    type: 'sma',
                    period: period,
                    series: smaSeries,
                    color: color
                });
                
                // Update chart
                mainChart.applyOptions({
                    watermark: {
                        visible: true,
                        fontSize: 12,
                        horzAlign: 'left',
                        vertAlign: 'bottom',
                        color: 'rgba(255, 255, 255, 0.5)',
                        text: `SMA(${period}): ${smaValues[smaValues.length - 1].toFixed(2)}`
                    }
                });
            })
            .catch(error => {
                console.error('Error adding SMA:', error);
                removeIndicatorBadge(indicatorId);
            });
    } catch (e) {
        console.error('Error in addSMA:', e);
    }
}

/**
 * Calculate SMA values
 * @param {Array} prices - Array of price values
 * @param {number} period - Period for SMA calculation
 * @returns {Array} - SMA values
 */
function calculateSMA(prices, period) {
    const smaValues = [];
    
    for (let i = 0; i < prices.length; i++) {
        if (i < period - 1) {
            smaValues.push(null);
            continue;
        }
        
        let sum = 0;
        for (let j = 0; j < period; j++) {
            sum += prices[i - j];
        }
        
        smaValues.push(sum / period);
    }
    
    return smaValues;
}

/**
 * Add VWAP indicator to the chart
 */
function addVWAP(color = '#9C27B0') {
    try {
        // Track loading state
        const indicatorId = 'vwap';
        
        // Check if this indicator is already active
        if (activeIndicators.some(i => i.id === indicatorId)) {
            console.log('VWAP is already on the chart');
            return;
        }
        
        // Add indicator badge
        addIndicatorBadge('VWAP', color, indicatorId);
        
        // Fetch the most recent data
        fetch(`/api/price-data/${currentSymbol}?timeframe=${currentTimeframe}`)
            .then(response => response.json())
            .then(data => {
                if (!data || !data.length) {
                    console.error('No data available for VWAP calculation');
                    return;
                }
                
                // Calculate VWAP
                const vwapValues = calculateVWAP(data);
                
                // Format data for TradingView
                const vwapData = data.map((item, index) => ({
                    time: item.time,
                    value: vwapValues[index]
                }));
                
                // Create VWAP series
                const vwapSeries = mainChart.addLineSeries({
                    color: color,
                    lineWidth: 2,
                    lineStyle: 2, // LightweightCharts.LineStyle.Dashed
                    priceScaleId: 'right'
                });
                
                vwapSeries.setData(vwapData);
                
                // Store for later removal
                activeIndicators.push({
                    id: indicatorId,
                    type: 'vwap',
                    series: vwapSeries,
                    color: color
                });
                
                // Update chart
                mainChart.applyOptions({
                    watermark: {
                        visible: true,
                        fontSize: 12,
                        horzAlign: 'left',
                        vertAlign: 'bottom',
                        color: 'rgba(255, 255, 255, 0.5)',
                        text: `VWAP: ${vwapValues[vwapValues.length - 1].toFixed(2)}`
                    }
                });
            })
            .catch(error => {
                console.error('Error adding VWAP:', error);
                removeIndicatorBadge(indicatorId);
            });
    } catch (e) {
        console.error('Error in addVWAP:', e);
    }
}

/**
 * Calculate VWAP values
 * @param {Array} data - Array of price and volume data
 * @returns {Array} - VWAP values
 */
function calculateVWAP(data) {
    let cumulativeTPV = 0;
    let cumulativeVolume = 0;
    const vwapValues = [];
    
    for (let i = 0; i < data.length; i++) {
        const typicalPrice = (parseFloat(data[i].high) + parseFloat(data[i].low) + parseFloat(data[i].close)) / 3;
        const volume = parseFloat(data[i].volume);
        
        cumulativeTPV += typicalPrice * volume;
        cumulativeVolume += volume;
        
        vwapValues.push(cumulativeVolume ? cumulativeTPV / cumulativeVolume : null);
    }
    
    return vwapValues;
}

/**
 * Add indicator badge to the toolbar
 */
function addIndicatorBadge(name, color, id) {
    const activeIndicatorsEl = document.getElementById('activeIndicators');
    if (!activeIndicatorsEl) return;
    
    const badge = document.createElement('span');
    badge.className = 'indicator-badge';
    badge.dataset.id = id;
    badge.innerHTML = `
        <span style="color: ${color};">●</span>
        ${name}
        <button class="remove-indicator" data-id="${id}">&times;</button>
    `;
    
    activeIndicatorsEl.appendChild(badge);
    
    // Add event listener for removal
    const removeBtn = badge.querySelector('.remove-indicator');
    removeBtn.addEventListener('click', (e) => {
        const indicatorId = e.target.dataset.id;
        removeIndicator(indicatorId);
    });
}

/**
 * Remove indicator badge from the toolbar
 */
function removeIndicatorBadge(id) {
    const badge = document.querySelector(`.indicator-badge[data-id="${id}"]`);
    if (badge) {
        badge.parentNode.removeChild(badge);
    }
}

/**
 * Remove indicator from the chart
 */
function removeIndicator(id) {
    // Find the indicator in the active indicators
    const indicatorIndex = activeIndicators.findIndex(i => i.id === id);
    
    if (indicatorIndex === -1) {
        console.error(`Indicator ${id} not found`);
        return;
    }
    
    const indicator = activeIndicators[indicatorIndex];
    
    // Remove the series from the chart
    mainChart.removeSeries(indicator.series);
    
    // Remove from active indicators
    activeIndicators.splice(indicatorIndex, 1);
    
    // Remove the badge
    removeIndicatorBadge(id);
    
    // Reset watermark if no indicators left
    if (activeIndicators.length === 0) {
        mainChart.applyOptions({
            watermark: {
                visible: false
            }
        });
    }
}

/**
 * Setup drawing tools
 */
function setupDrawingTools() {
    // Get all drawing tool buttons
    const drawingTools = document.querySelectorAll('.drawing-tool');
    if (!drawingTools.length) {
        console.log('No drawing tools found');
        return;
    }
    
    // Set cursor as default active tool
    const cursorTool = document.querySelector('.drawing-tool[data-tool="cursor"]');
    if (cursorTool) {
        cursorTool.classList.add('active');
    }
    
    // Add click event listeners to each tool
    drawingTools.forEach(tool => {
        tool.addEventListener('click', () => {
            // Remove active class from all tools
            drawingTools.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tool
            tool.classList.add('active');
            
            // Set active tool
            const toolType = tool.dataset.tool;
            drawingToolState.activeTool = toolType;
            
            // Handle special tools
            if (toolType === 'reset') {
                clearDrawings();
                // Reset back to cursor after clearing
                drawingToolState.activeTool = 'cursor';
                cursorTool.classList.add('active');
                tool.classList.remove('active');
            }
            
            console.log(`Active tool set to: ${drawingToolState.activeTool}`);
        });
    });
    
    // Add mouse event listeners to chart for drawing
    const chartContainer = document.getElementById('mainChart');
    if (chartContainer) {
        // Mouse down event
        chartContainer.addEventListener('mousedown', handleDrawingMouseDown);
        
        // Mouse move event
        chartContainer.addEventListener('mousemove', handleDrawingMouseMove);
        
        // Mouse up event
        chartContainer.addEventListener('mouseup', handleDrawingMouseUp);
        
        // Mouse leave event - finish drawing if cursor leaves chart
        chartContainer.addEventListener('mouseleave', handleDrawingMouseUp);
    }
}

/**
 * Handle mouse down event for drawing
 */
function handleDrawingMouseDown(e) {
    if (drawingToolState.activeTool === 'cursor') return;
    
    // Get chart coordinates
    const rect = mainChart.timeScale().getVisibleLogicalRange();
    const price = mainChart.priceScale('right').coordinateToPrice(e.offsetY);
    const time = mainChart.timeScale().coordinateToTime(e.offsetX);
    
    if (!price || !time) return;
    
    // Start drawing
    drawingToolState.isDrawing = true;
    drawingToolState.startPoint = { price, time };
    
    // For text tool, show a text input
    if (drawingToolState.activeTool === 'text') {
        showTextInput(e.clientX, e.clientY);
    }
}

/**
 * Handle mouse move event for drawing
 */
function handleDrawingMouseMove(e) {
    if (!drawingToolState.isDrawing || drawingToolState.activeTool === 'cursor' || drawingToolState.activeTool === 'text') return;
    
    // Get chart coordinates
    const price = mainChart.priceScale('right').coordinateToPrice(e.offsetY);
    const time = mainChart.timeScale().coordinateToTime(e.offsetX);
    
    if (!price || !time) return;
    
    // If we have an active drawing, remove it
    if (drawingToolState.activeDrawing) {
        mainChart.removeSeries(drawingToolState.activeDrawing);
    }
    
    // Draw based on tool type
    switch (drawingToolState.activeTool) {
        case 'line':
            drawLine(drawingToolState.startPoint, { price, time }, true);
            break;
        case 'rectangle':
            drawRectangle(drawingToolState.startPoint, { price, time }, true);
            break;
        case 'fibonacci':
            drawFibonacci(drawingToolState.startPoint, { price, time }, true);
            break;
    }
}

/**
 * Handle mouse up event for drawing
 */
function handleDrawingMouseUp(e) {
    if (!drawingToolState.isDrawing || drawingToolState.activeTool === 'cursor') return;
    
    // Get chart coordinates
    const price = mainChart.priceScale('right').coordinateToPrice(e.offsetY);
    const time = mainChart.timeScale().coordinateToTime(e.offsetX);
    
    if (!price || !time || !drawingToolState.startPoint) {
        drawingToolState.isDrawing = false;
        drawingToolState.activeDrawing = null;
        return;
    }
    
    // Finalize drawing based on tool type
    switch (drawingToolState.activeTool) {
        case 'line':
            drawLine(drawingToolState.startPoint, { price, time }, false);
            break;
        case 'rectangle':
            drawRectangle(drawingToolState.startPoint, { price, time }, false);
            break;
        case 'fibonacci':
            drawFibonacci(drawingToolState.startPoint, { price, time }, false);
            break;
    }
    
    // Reset drawing state
    drawingToolState.isDrawing = false;
    drawingToolState.activeDrawing = null;
}

/**
 * Draw a line on the chart
 */
function drawLine(start, end, isPreview) {
    // Create line series
    const lineSeries = mainChart.addLineSeries({
        color: 'rgba(255, 255, 255, 0.8)',
        lineWidth: 2,
        lastValueVisible: false,
        priceLineVisible: false,
    });
    
    // Set line data
    lineSeries.setData([
        { time: start.time, value: start.price },
        { time: end.time, value: end.price }
    ]);
    
    // If this is a preview, store reference for later removal
    if (isPreview) {
        drawingToolState.activeDrawing = lineSeries;
    } else {
        // Store the completed line
        drawingToolState.lines.push(lineSeries);
    }
}

/**
 * Draw a rectangle on the chart
 */
function drawRectangle(start, end, isPreview) {
    // Calculate the corners
    const topLeft = {
        time: Math.min(start.time, end.time),
        value: Math.max(start.price, end.price)
    };
    
    const topRight = {
        time: Math.max(start.time, end.time),
        value: Math.max(start.price, end.price)
    };
    
    const bottomLeft = {
        time: Math.min(start.time, end.time),
        value: Math.min(start.price, end.price)
    };
    
    const bottomRight = {
        time: Math.max(start.time, end.time),
        value: Math.min(start.price, end.price)
    };
    
    // Create rectangle series (4 lines)
    const rectSeries = [];
    
    // Top line
    const topLine = mainChart.addLineSeries({
        color: 'rgba(255, 255, 255, 0.8)',
        lineWidth: 2,
        lastValueVisible: false,
        priceLineVisible: false,
    });
    
    topLine.setData([topLeft, topRight]);
    rectSeries.push(topLine);
    
    // Right line
    const rightLine = mainChart.addLineSeries({
        color: 'rgba(255, 255, 255, 0.8)',
        lineWidth: 2,
        lastValueVisible: false,
        priceLineVisible: false,
    });
    
    rightLine.setData([topRight, bottomRight]);
    rectSeries.push(rightLine);
    
    // Bottom line
    const bottomLine = mainChart.addLineSeries({
        color: 'rgba(255, 255, 255, 0.8)',
        lineWidth: 2,
        lastValueVisible: false,
        priceLineVisible: false,
    });
    
    bottomLine.setData([bottomLeft, bottomRight]);
    rectSeries.push(bottomLine);
    
    // Left line
    const leftLine = mainChart.addLineSeries({
        color: 'rgba(255, 255, 255, 0.8)',
        lineWidth: 2,
        lastValueVisible: false,
        priceLineVisible: false,
    });
    
    leftLine.setData([topLeft, bottomLeft]);
    rectSeries.push(leftLine);
    
    // If this is a preview, store reference for later removal
    if (isPreview) {
        drawingToolState.activeDrawing = rectSeries;
    } else {
        // Store the completed rectangle
        drawingToolState.rectangles.push(rectSeries);
    }
}

/**
 * Draw Fibonacci levels on the chart
 */
function drawFibonacci(start, end, isPreview) {
    // Calculate price range
    const priceMin = Math.min(start.price, end.price);
    const priceMax = Math.max(start.price, end.price);
    const priceRange = priceMax - priceMin;
    
    // Fibonacci levels (0, 0.236, 0.382, 0.5, 0.618, 0.786, 1)
    const fibLevels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
    const fibColors = [
        'rgba(255, 255, 255, 0.8)',  // 0
        'rgba(255, 152, 0, 0.8)',    // 0.236
        'rgba(76, 175, 80, 0.8)',    // 0.382
        'rgba(33, 150, 243, 0.8)',   // 0.5
        'rgba(156, 39, 176, 0.8)',   // 0.618
        'rgba(239, 83, 80, 0.8)',    // 0.786
        'rgba(255, 255, 255, 0.8)'   // 1
    ];
    
    // Create series for each level
    const fibSeries = [];
    
    for (let i = 0; i < fibLevels.length; i++) {
        const level = fibLevels[i];
        const price = end.price > start.price ? 
            priceMax - (priceRange * level) : 
            priceMin + (priceRange * level);
        
        // Create line series
        const lineSeries = mainChart.addLineSeries({
            color: fibColors[i],
            lineWidth: 1,
            lastValueVisible: true,
            priceLineVisible: false,
            title: `Fib ${level.toFixed(3)}`
        });
        
        // Set line data
        lineSeries.setData([
            { time: Math.min(start.time, end.time), value: price },
            { time: Math.max(start.time, end.time), value: price }
        ]);
        
        fibSeries.push(lineSeries);
    }
    
    // If this is a preview, store reference for later removal
    if (isPreview) {
        drawingToolState.activeDrawing = fibSeries;
    } else {
        // Store the completed fibonacci levels
        drawingToolState.fibonacciLevels.push(fibSeries);
    }
}

/**
 * Show text input for adding text to chart
 */
function showTextInput(x, y) {
    // Create input element
    const textInput = document.createElement('input');
    textInput.type = 'text';
    textInput.className = 'chart-text-input';
    textInput.style.position = 'absolute';
    textInput.style.left = x + 'px';
    textInput.style.top = y + 'px';
    textInput.style.zIndex = '1000';
    
    // Add to body
    document.body.appendChild(textInput);
    
    // Focus input
    textInput.focus();
    
    // Handle enter key (confirm)
    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const text = textInput.value.trim();
            if (text) {
                // Add text to chart
                addTextToChart(drawingToolState.startPoint, text);
            }
            
            // Remove input
            document.body.removeChild(textInput);
        }
    });
    
    // Handle blur (cancel)
    textInput.addEventListener('blur', () => {
        document.body.removeChild(textInput);
    });
}

/**
 * Add text note to chart
 */
function addTextToChart(point, text) {
    // Create text series (using candlestick series with a marker)
    const textSeries = mainChart.addLineSeries({
        lastValueVisible: false,
        priceLineVisible: false,
    });
    
    // Set data
    textSeries.setMarkers([
        {
            time: point.time,
            position: 'aboveBar',
            color: 'rgba(255, 255, 255, 0.8)',
            shape: 'circle',
            size: 1,
            text
        }
    ]);
    
    // Store the text note
    drawingToolState.textNotes.push(textSeries);
}

/**
 * Clear all drawings from the chart
 */
function clearDrawings() {
    // Remove lines
    drawingToolState.lines.forEach(line => {
        mainChart.removeSeries(line);
    });
    drawingToolState.lines = [];
    
    // Remove rectangles
    drawingToolState.rectangles.forEach(rect => {
        rect.forEach(line => mainChart.removeSeries(line));
    });
    drawingToolState.rectangles = [];
    
    // Remove fibonacci levels
    drawingToolState.fibonacciLevels.forEach(fib => {
        fib.forEach(line => mainChart.removeSeries(line));
    });
    drawingToolState.fibonacciLevels = [];
    
    // Remove text notes
    drawingToolState.textNotes.forEach(text => {
        mainChart.removeSeries(text);
    });
    drawingToolState.textNotes = [];
} 