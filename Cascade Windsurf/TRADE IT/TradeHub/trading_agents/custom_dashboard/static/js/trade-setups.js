/**
 * Trade Setups - Handles fetching and displaying trade setups in a social media style feed
 */

// Global variables
let setupsData = [];
let currentFilters = {
    direction: 'all'
};

// DOM elements
let setupsList;
let loadingIndicator;
let filterForm;
let directionFilter;
let refreshButton;
let resetButton;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    setupsList = document.getElementById('setups-list');
    loadingIndicator = document.getElementById('loading-indicator');
    filterForm = document.getElementById('filter-form');
    directionFilter = document.getElementById('direction-filter');
    refreshButton = document.querySelector('.refresh-btn');
    resetButton = document.querySelector('.reset-btn');
    
    // Set up event listeners
    if (filterForm) {
        filterForm.addEventListener('submit', handleFilterSubmit);
    }
    
    if (resetButton) {
        resetButton.addEventListener('click', resetFilters);
    }
    
    if (refreshButton) {
        refreshButton.addEventListener('click', fetchSetups);
    }
    
    // Initially fetch setups
    fetchSetups();
    
    // Set up socket connection for real-time updates
    setupSocketConnection();
});

/**
 * Fetch trade setups from the API
 */
function fetchSetups() {
    // Show loading state
    if (loadingIndicator) {
        loadingIndicator.classList.remove('hidden');
    }
    
    if (setupsList) {
        setupsList.innerHTML = '';
    }
    
    // Prepare API URL with current filters
    let url = '/api/setups?';
    if (currentFilters.direction !== 'all') url += `direction=${currentFilters.direction}&`;
    
    // Always focus on sweep engulfing patterns
    url += 'setup_type=sweep_engulfing_confirmed&';
    url += 'limit=50';
    
    // Fetch data from API
    fetch(url)
        .then(response => response.json())
        .then(data => {
            setupsData = data;
            renderSetups();
        })
        .catch(error => {
            console.error('Error fetching setups:', error);
            if (setupsList) {
                setupsList.innerHTML = '<div class="error-message">Failed to load trade setups. Please try again.</div>';
            }
        })
        .finally(() => {
            if (loadingIndicator) {
                loadingIndicator.classList.add('hidden');
            }
        });
}

/**
 * Handle filter form submission
 */
function handleFilterSubmit(event) {
    event.preventDefault();
    
    // Update current filters
    currentFilters.direction = directionFilter.value;
    
    // Fetch with new filters
    fetchSetups();
}

/**
 * Reset filters to default values
 */
function resetFilters() {
    directionFilter.value = 'all';
    currentFilters.direction = 'all';
    fetchSetups();
}

/**
 * Render the setups in the container
 */
function renderSetups() {
    if (!setupsList) return;
    
    // Clear current content
    setupsList.innerHTML = '';
    
    // Check if we have data
    if (!setupsData || setupsData.length === 0) {
        setupsList.innerHTML = '<div class="no-setups-message">No trade setups found. Check back later or try different filters.</div>';
        return;
    }
    
    // Render each setup as a card
    setupsData.forEach(setup => {
        const card = createSetupCard(setup);
        setupsList.appendChild(card);
    });
}

/**
 * Create a card element for a trade setup
 */
function createSetupCard(setup) {
    const card = document.createElement('div');
    card.className = `setup-card ${setup.direction}`;
    card.dataset.id = setup.id;
    
    const formattedTime = new Date(setup.date_identified || setup.timestamp).toLocaleString();
    const riskReward = (Math.abs(setup.target - setup.entry_price) / Math.abs(setup.stop_loss - setup.entry_price)).toFixed(2);
    
    // Create the card header
    const cardHeader = document.createElement('div');
    cardHeader.className = 'setup-card-header';
    
    // Symbol and timeframe
    const symbolTimeframe = document.createElement('div');
    symbolTimeframe.className = 'symbol-timeframe';
    symbolTimeframe.innerHTML = `
        <span class="symbol">${setup.symbol}</span>
        <span class="timeframe">${setup.timeframe}</span>
    `;
    
    // Direction indicator
    const directionIndicator = document.createElement('div');
    directionIndicator.className = `direction-indicator ${setup.direction}`;
    directionIndicator.innerHTML = `
        <i class="fas fa-${setup.direction === 'bullish' ? 'arrow-up' : 'arrow-down'}"></i>
        <span>${setup.direction.toUpperCase()}</span>
    `;
    
    cardHeader.appendChild(symbolTimeframe);
    cardHeader.appendChild(directionIndicator);
    
    // Create the card content
    const cardContent = document.createElement('div');
    cardContent.className = 'setup-card-content';
    
    // Setup type with icon - always display as SWEEP ENGULFING CONFIRMED
    const setupType = document.createElement('div');
    setupType.className = 'setup-type';
    setupType.innerHTML = `
        <i class="fas fa-crosshairs"></i>
        <span>SWEEP ENGULFING CONFIRMED</span>
    `;
    
    // Price levels
    const priceLevels = document.createElement('div');
    priceLevels.className = 'price-levels';
    priceLevels.innerHTML = `
        <div class="price-level entry">
            <span class="label">ENTRY</span>
            <span class="value">${setup.entry_price.toFixed(2)}</span>
        </div>
        <div class="price-level stop">
            <span class="label">STOP</span>
            <span class="value">${setup.stop_loss.toFixed(2)}</span>
        </div>
        <div class="price-level target">
            <span class="label">TARGET</span>
            <span class="value">${setup.target.toFixed(2)}</span>
        </div>
    `;
    
    // Risk/Reward and confirmation type
    const details = document.createElement('div');
    details.className = 'setup-details';
    details.innerHTML = `
        <div class="risk-reward">
            <span class="label">RISK/REWARD</span>
            <span class="value">${riskReward}x</span>
        </div>
        <div class="confirmation">
            <span class="label">CONFIRMATION</span>
            <span class="value"><i class="fas fa-check-circle"></i></span>
        </div>
    `;
    
    // Add all content elements to the card
    cardContent.appendChild(setupType);
    cardContent.appendChild(priceLevels);
    cardContent.appendChild(details);
    
    // Create the card footer
    const cardFooter = document.createElement('div');
    cardFooter.className = 'setup-card-footer';
    
    // Timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'timestamp';
    timestamp.innerHTML = `
        <i class="far fa-clock"></i>
        <span>${formattedTime}</span>
    `;
    
    // Actions
    const actions = document.createElement('div');
    actions.className = 'setup-actions';
    
    // View details button
    const viewButton = document.createElement('button');
    viewButton.className = 'view-btn';
    viewButton.innerHTML = '<i class="far fa-eye"></i> View';
    viewButton.addEventListener('click', () => viewSetupDetails(setup.id));
    
    // Status button
    const statusButton = document.createElement('button');
    statusButton.className = `status-btn ${setup.status === 'triggered' ? 'triggered' : ''}`;
    statusButton.innerHTML = `
        <i class="fas fa-${getStatusIcon(setup.status)}"></i>
        ${capitalize(setup.status)}
    `;
    statusButton.addEventListener('click', () => {
        const newStatus = setup.status === 'active' ? 'triggered' : 'active';
        markSetupStatus(setup.id, newStatus);
    });
    
    actions.appendChild(viewButton);
    actions.appendChild(statusButton);
    
    cardFooter.appendChild(timestamp);
    cardFooter.appendChild(actions);
    
    // Add all sections to the card
    card.appendChild(cardHeader);
    card.appendChild(cardContent);
    card.appendChild(cardFooter);
    
    return card;
}

/**
 * Get icon name for a setup status
 */
function getStatusIcon(status) {
    switch (status) {
        case 'triggered': return 'check-circle';
        case 'completed': return 'flag-checkered';
        case 'expired': return 'times-circle';
        default: return 'circle';
    }
}

/**
 * Capitalize first letter of a string
 */
function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Set up socket connection for real-time updates
 */
function setupSocketConnection() {
    if (typeof io !== 'undefined') {
        const socket = io.connect();
        
        // Listen for new setup events
        socket.on('new_setup', (setupData) => {
            // Only add if it's a sweep engulfing pattern
            if (setupData.setup_type === 'sweep_engulfing_confirmed') {
                // Add to our data
                setupsData.unshift(setupData);
                
                // Re-render with new data
                renderSetups();
                
                // Show notification
                showNotification(`New ${setupData.direction} setup on ${setupData.symbol}`);
            }
        });
        
        // Listen for setup status updates
        socket.on('setup_update', (updateData) => {
            // Find and update the setup
            const setupIndex = setupsData.findIndex(s => s.id === updateData.id);
            if (setupIndex !== -1) {
                setupsData[setupIndex] = {...setupsData[setupIndex], ...updateData};
                renderSetups();
            }
        });
    }
}

/**
 * Show browser notification for new setups
 */
function showNotification(message) {
    // Check if browser notifications are supported
    if ('Notification' in window) {
        // Check if permission is already granted
        if (Notification.permission === 'granted') {
            // Create and show notification
            new Notification('Trade Hub Setup', {
                body: message,
                icon: '/static/img/logo.png'
            });
        } 
        // Check if permission is not denied
        else if (Notification.permission !== 'denied') {
            // Request permission
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification('Trade Hub Setup', {
                        body: message,
                        icon: '/static/img/logo.png'
                    });
                }
            });
        }
    }
}

/**
 * View details for a specific setup
 */
function viewSetupDetails(setupId) {
    const setup = setupsData.find(s => s.id === setupId);
    if (setup) {
        // TODO: Implement a chart view modal showing the setup
        console.log('Viewing setup details:', setup);
        alert(`Viewing setup details for ${setup.symbol} ${setup.direction} pattern`);
    }
}

/**
 * Update the status of a setup
 */
function markSetupStatus(setupId, newStatus) {
    // Find the setup
    const setup = setupsData.find(s => s.id === setupId);
    if (!setup) return;
    
    // Prepare request data
    const updateData = {
        status: newStatus,
        updated_at: new Date().toISOString()
    };
    
    // Send update to server
    fetch(`/api/setups/${setupId}`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(data => {
        // Update local data
        const setupIndex = setupsData.findIndex(s => s.id === setupId);
        if (setupIndex !== -1) {
            setupsData[setupIndex] = {...setupsData[setupIndex], ...data};
            renderSetups();
        }
    })
    .catch(error => {
        console.error('Error updating setup status:', error);
    });
}
