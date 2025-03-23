/**
 * Trade Hub Dashboard - Main JavaScript
 * Handles UI interactions and general functionality
 */

document.addEventListener('DOMContentLoaded', () => {
    // Handle responsive sidebar toggle
    initSidebar();
    
    // Initialize dark/light mode toggle
    initThemeToggle();
    
    // Initialize widgets
    initWidgets();
    
    // Initialize chatbot
    initChatbot();
});

/**
 * Initialize sidebar functionality
 */
function initSidebar() {
    // Add mobile menu toggle for smaller screens
    const body = document.querySelector('body');
    const sidebarToggle = document.createElement('button');
    sidebarToggle.classList.add('sidebar-toggle');
    sidebarToggle.innerHTML = '<i class="fas fa-bars"></i>';
    body.appendChild(sidebarToggle);
    
    // Toggle sidebar on click
    sidebarToggle.addEventListener('click', () => {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.toggle('sidebar-open');
    });
    
    // Close sidebar when clicking outside
    document.addEventListener('click', (event) => {
        const sidebar = document.querySelector('.sidebar');
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        
        if (sidebar.classList.contains('sidebar-open') && 
            !sidebar.contains(event.target) && 
            event.target !== sidebarToggle &&
            !sidebarToggle.contains(event.target)) {
            sidebar.classList.remove('sidebar-open');
        }
    });
}

/**
 * Initialize theme toggle functionality
 */
function initThemeToggle() {
    const themeToggle = document.querySelector('.theme-toggle');
    
    // Check for saved theme preference or use device preference
    const savedTheme = localStorage.getItem('tradeHubTheme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial theme
    if (savedTheme === 'light' || (!savedTheme && !prefersDark)) {
        document.documentElement.classList.add('light-theme');
        themeToggle.querySelector('i').classList.replace('fa-moon', 'fa-sun');
        themeToggle.querySelector('span').textContent = 'Light Mode';
    }
    
    // Toggle theme on click
    themeToggle.addEventListener('click', () => {
        document.documentElement.classList.toggle('light-theme');
        
        // Update icon and text
        const icon = themeToggle.querySelector('i');
        const text = themeToggle.querySelector('span');
        
        if (document.documentElement.classList.contains('light-theme')) {
            icon.classList.replace('fa-moon', 'fa-sun');
            text.textContent = 'Light Mode';
            localStorage.setItem('tradeHubTheme', 'light');
        } else {
            icon.classList.replace('fa-sun', 'fa-moon');
            text.textContent = 'Dark Mode';
            localStorage.setItem('tradeHubTheme', 'dark');
        }
    });
}

/**
 * Initialize widget functionality
 */
function initWidgets() {
    // Make widgets resizable
    const widgets = document.querySelectorAll('.widget');
    
    widgets.forEach(widget => {
        // Add expand/collapse functionality
        const expandButton = widget.querySelector('.btn-icon');
        if (expandButton) {
            expandButton.addEventListener('click', () => {
                widget.classList.toggle('widget-expanded');
                
                // Update icon
                const icon = expandButton.querySelector('i');
                if (widget.classList.contains('widget-expanded')) {
                    icon.classList.replace('fa-expand', 'fa-compress');
                } else {
                    icon.classList.replace('fa-compress', 'fa-expand');
                }
                
                // Resize charts if expanded
                if (window.mainChart && widget.classList.contains('main-chart')) {
                    setTimeout(() => {
                        const container = document.getElementById('mainChart');
                        window.mainChart.resize(container.clientWidth, container.clientHeight);
                    }, 300);
                }
                
                if (window.orderFlowChart && widget.classList.contains('order-flow')) {
                    setTimeout(() => {
                        const container = document.getElementById('orderFlowChart');
                        window.orderFlowChart.resize(container.clientWidth, container.clientHeight);
                    }, 300);
                }
            });
        }
    });
}

/**
 * Initialize chatbot functionality
 */
function initChatbot() {
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotSendBtn = document.getElementById('chatbotSendBtn');
    const chatbotMessages = document.getElementById('chatbotMessages');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    
    // Handle send button click
    chatbotSendBtn.addEventListener('click', () => {
        sendChatbotMessage();
    });
    
    // Handle enter key press in input
    chatbotInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatbotMessage();
        }
    });
    
    // Handle suggestion buttons
    suggestionButtons.forEach(button => {
        button.addEventListener('click', () => {
            const message = button.textContent;
            chatbotInput.value = message;
            sendChatbotMessage();
        });
    });
    
    /**
     * Send message to chatbot
     */
    function sendChatbotMessage() {
        const message = chatbotInput.value.trim();
        
        if (message) {
            // Add user message to chat
            addMessageToChat(message, 'user');
            
            // Clear input
            chatbotInput.value = '';
            
            // Process message (for now, just show placeholder responses)
            processChatbotMessage(message);
        }
    }
    
    /**
     * Add message to chat
     */
    function addMessageToChat(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', sender);
        
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${message}</p>
            </div>
        `;
        
        chatbotMessages.appendChild(messageElement);
        
        // Scroll to bottom
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
    
    /**
     * Process chatbot message and generate response
     * This is a placeholder for the actual NLP functionality
     */
    function processChatbotMessage(message) {
        // Convert message to lowercase for easier matching
        const lowerMessage = message.toLowerCase();
        
        // Simulate typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('chat-message', 'bot', 'typing-indicator');
        typingIndicator.innerHTML = `
            <div class="message-content">
                <p>Typing<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></p>
            </div>
        `;
        chatbotMessages.appendChild(typingIndicator);
        
        // Simulate response time
        setTimeout(() => {
            // Remove typing indicator
            typingIndicator.remove();
            
            // Generate response based on message content
            let response;
            
            if (lowerMessage.includes('ema') || lowerMessage.includes('moving average')) {
                response = "I've added the EMA indicator to your chart.";
                
                // Actually add the EMA to the chart if the charts.js function exists
                if (typeof window.addEMA === 'function') {
                    const match = lowerMessage.match(/\d+/);
                    const period = match ? parseInt(match[0]) : 20;
                    window.addEMA(period, '#FFEB3B');
                }
            } 
            else if (lowerMessage.includes('high') && lowerMessage.includes('low')) {
                response = "I've highlighted today's high and low prices on the chart.";
                // This would be implemented later with actual functionality
            }
            else if (lowerMessage.includes('fair value') || lowerMessage.includes('gap')) {
                response = "I've identified and marked the fair value gaps on your chart.";
                // This would be implemented later with actual functionality
            }
            else if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
                response = "Hello! How can I help with your chart analysis today?";
            }
            else {
                // Default response
                response = "I'll process your request: \"" + message + "\". This feature will be fully implemented soon.";
            }
            
            // Add response to chat
            addMessageToChat(response, 'bot');
            
            // Optional: Add a follow-up suggestion
            if (!lowerMessage.includes('hello') && !lowerMessage.includes('hi')) {
                setTimeout(() => {
                    addMessageToChat("Would you like me to analyze this pattern or add another indicator?", 'bot');
                }, 1000);
            }
        }, 1500);
    }
}

/**
 * Show a notification message
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.classList.add('notification', `notification-${type}`);
    notification.innerHTML = `
        <div class="notification-icon">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
        </div>
        <div class="notification-content">
            <p>${message}</p>
        </div>
        <button class="notification-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add notification to the DOM
    const notificationsContainer = document.querySelector('.notifications-container') || createNotificationsContainer();
    notificationsContainer.appendChild(notification);
    
    // Add close button functionality
    const closeButton = notification.querySelector('.notification-close');
    closeButton.addEventListener('click', () => {
        notification.classList.add('notification-hiding');
        setTimeout(() => {
            notification.remove();
            
            // Remove container if empty
            if (notificationsContainer.children.length === 0) {
                notificationsContainer.remove();
            }
        }, 300);
    });
    
    // Automatically remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.classList.add('notification-hiding');
            setTimeout(() => {
                notification.remove();
                
                // Remove container if empty
                if (notificationsContainer.children.length === 0) {
                    notificationsContainer.remove();
                }
            }, 300);
        }
    }, 5000);
}

/**
 * Create a container for notifications
 */
function createNotificationsContainer() {
    const container = document.createElement('div');
    container.classList.add('notifications-container');
    document.body.appendChild(container);
    return container;
}

/**
 * Format a date as a string
 */
function formatDate(date) {
    return new Date(date).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

/**
 * Add CSS style for light theme and notifications
 */
(function addAdditionalStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Light theme */
        .light-theme {
            --bg-primary: #f5f5f5;
            --bg-secondary: #ffffff;
            --bg-tertiary: #f0f0f0;
            --text-primary: #333333;
            --text-secondary: #666666;
            --border-color: #e0e0e0;
            --hover-color: #e5e5e5;
        }
        
        /* Sidebar toggle for mobile */
        .sidebar-toggle {
            display: none;
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 1000;
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius-sm);
            width: 40px;
            height: 40px;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            cursor: pointer;
            color: var(--text-primary);
        }
        
        /* Widget expanded state */
        .widget-expanded {
            position: fixed;
            top: 20px;
            left: 20px;
            right: 20px;
            bottom: 20px;
            z-index: 1000;
            width: auto !important;
            height: auto !important;
        }
        
        /* Notifications */
        .notifications-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 2000;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 400px;
        }
        
        .notification {
            display: flex;
            align-items: center;
            gap: 10px;
            background-color: var(--bg-secondary);
            border-radius: var(--border-radius-md);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            padding: 15px;
            animation: slideIn 0.3s ease-out forwards;
        }
        
        .notification-hiding {
            animation: slideOut 0.3s ease-in forwards;
        }
        
        .notification-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            flex-shrink: 0;
        }
        
        .notification-content {
            flex: 1;
        }
        
        .notification-close {
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: none;
            border: none;
            cursor: pointer;
            color: var(--text-secondary);
        }
        
        .notification-success .notification-icon {
            color: var(--accent-green);
        }
        
        .notification-error .notification-icon {
            color: var(--accent-red);
        }
        
        .notification-info .notification-icon {
            color: var(--accent-blue);
        }
        
        /* Analysis items */
        .analysis-section {
            margin-bottom: 1.5rem;
        }
        
        .analysis-section h3 {
            margin-bottom: 0.5rem;
        }
        
        .analysis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 1rem;
        }
        
        .analysis-item {
            display: flex;
            flex-direction: column;
            padding: 0.5rem;
            background-color: var(--bg-tertiary);
            border-radius: var(--border-radius-sm);
        }
        
        .analysis-label {
            font-size: var(--font-size-xs);
            color: var(--text-secondary);
            margin-bottom: 0.25rem;
        }
        
        .analysis-value {
            font-size: var(--font-size-md);
            font-weight: 500;
        }
        
        .analysis-value.bullish {
            color: var(--accent-green);
        }
        
        .analysis-value.bearish {
            color: var(--accent-red);
        }
        
        .analysis-value.overbought {
            color: var(--accent-red);
        }
        
        .analysis-value.oversold {
            color: var(--accent-green);
        }
        
        /* Mobile styles */
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                transition: transform 0.3s ease;
                position: fixed;
                z-index: 1000;
                height: 100%;
            }
            
            .sidebar-open {
                transform: translateX(0);
            }
            
            .sidebar-toggle {
                display: flex;
            }
            
            .main-content {
                margin-left: 0;
            }
        }
        
        /* Animations */
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }

        /* Chatbot typing indicator */
        .typing-indicator .dot {
            animation: typingAnimation 1.4s infinite;
            display: inline-block;
        }
        
        .typing-indicator .dot:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator .dot:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typingAnimation {
            0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
            30% { opacity: 1; transform: translateY(-4px); }
        }
    `;
    document.head.appendChild(style);
})(); 