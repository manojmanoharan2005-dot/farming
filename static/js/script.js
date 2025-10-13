// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }
    
    // Initialize dashboard if on dashboard page
    if (document.querySelector('.dashboard')) {
        initializeDashboard();
    }
    
    // Auto-hide flash messages after 5 seconds
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (alert.parentElement) {
                alert.remove();
            }
        });
    }, 5000);
});

// Dashboard Functions
function initializeDashboard() {
    // Sidebar navigation
    initializeSidebarNavigation();
    
    // Start real-time updates
    startRealTimeUpdates();
    
    // Animate profit chart
    animateProfitChart();
}

function initializeSidebarNavigation() {
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    
    sidebarLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all links
            sidebarLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            link.classList.add('active');
            
            // Get section name
            const section = link.dataset.section || 'overview';
            
            // Show notification for non-overview sections
            if (section !== 'overview') {
                const feature = link.querySelector('span:last-child').textContent;
                showNotification(`${feature} section coming soon!`, 'info');
            }
        });
    });
}

function startRealTimeUpdates() {
    // Update weather every 30 seconds
    setInterval(updateWeather, 30000);
    
    // Update market prices every 60 seconds
    setInterval(updateMarketPrices, 60000);
}

function updateWeather() {
    fetch('/api/weather')
        .then(response => response.json())
        .then(data => {
            const tempElement = document.getElementById('temperature');
            const humidityElement = document.getElementById('humidity');
            const rainElement = document.getElementById('rain-chance');
            
            if (tempElement) tempElement.textContent = `${data.temperature}°C`;
            if (humidityElement) humidityElement.textContent = `Humidity: ${data.humidity}%`;
            if (rainElement) rainElement.textContent = `Rain: ${data.rain_chance}%`;
        })
        .catch(error => console.error('Error updating weather:', error));
}

function updateMarketPrices() {
    fetch('/api/market-prices')
        .then(response => response.json())
        .then(data => {
            const marketContainer = document.getElementById('market-prices');
            if (marketContainer) {
                marketContainer.innerHTML = `
                    <div class="price-item">
                        <span>Rice</span>
                        <span>₹${data.rice}/quintal</span>
                    </div>
                    <div class="price-item">
                        <span>Wheat</span>
                        <span>₹${data.wheat}/quintal</span>
                    </div>
                    <div class="price-item">
                        <span>Cotton</span>
                        <span>₹${data.cotton}/quintal</span>
                    </div>
                `;
            }
        })
        .catch(error => console.error('Error updating market prices:', error));
}

function animateProfitChart() {
    setTimeout(() => {
        const expenseBar = document.querySelector('.bar.expenses');
        const profitBar = document.querySelector('.bar.profit');
        
        if (expenseBar && profitBar) {
            expenseBar.style.height = '60%';
            profitBar.style.height = '80%';
        }
    }, 1000);
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `
        <div class="alert alert-${type}">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    
    // Add to flash messages container or create one
    let flashContainer = document.querySelector('.flash-messages');
    if (!flashContainer) {
        flashContainer = document.createElement('div');
        flashContainer.className = 'flash-messages';
        document.body.appendChild(flashContainer);
    }
    
    flashContainer.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Form validation for auth pages
function validateRegistrationForm() {
    const password = document.querySelector('input[name="password"]').value;
    const confirmPassword = document.querySelector('input[name="confirm_password"]').value;
    
    if (password !== confirmPassword) {
        showNotification('Passwords do not match!', 'error');
        return false;
    }
    
    return true;
}

// Add form validation event listeners
document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.querySelector('form[method="POST"]');
    const confirmPasswordInput = document.querySelector('input[name="confirm_password"]');
    
    if (registerForm && confirmPasswordInput) {
        registerForm.addEventListener('submit', function(e) {
            if (!validateRegistrationForm()) {
                e.preventDefault();
            }
        });
    }
});
