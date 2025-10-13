document.addEventListener('DOMContentLoaded', function() {
    // Initialize chart
    initializeProfitChart();
    
    // Start real-time updates
    startRealTimeUpdates();
    
    // Sidebar navigation
    initializeSidebarNav();
});

function initializeProfitChart() {
    const ctx = document.getElementById('profitChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'Profit',
                data: [65, 59, 80, 81, 56, 85],
                backgroundColor: '#10b981',
                borderRadius: 4
            }, {
                label: 'Expenses',
                data: [45, 49, 60, 71, 46, 65],
                backgroundColor: '#ef4444',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#f1f5f9'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
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
            document.getElementById('temperature').textContent = `${data.temperature}°C`;
            document.getElementById('humidity').textContent = `${data.humidity}%`;
            document.getElementById('rain-chance').textContent = `${data.rain_chance}%`;
        })
        .catch(error => console.error('Weather update failed:', error));
}

function updateMarketPrices() {
    fetch('/api/market-prices')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('market-prices');
            if (container && data) {
                const crops = Object.keys(data);
                let html = '';
                crops.forEach(crop => {
                    const change = Math.random() > 0.5 ? 'positive' : 'negative';
                    const changeValue = (Math.random() * 5).toFixed(1);
                    html += `
                        <div class="market-item">
                            <div class="market-crop">${crop.charAt(0).toUpperCase() + crop.slice(1)}</div>
                            <div class="market-price">₹${data[crop]}/quintal</div>
                            <div class="market-change ${change}">${change === 'positive' ? '+' : '-'}${changeValue}%</div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            }
        })
        .catch(error => console.error('Market prices update failed:', error));
}

function initializeSidebarNav() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all items
            navItems.forEach(nav => nav.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Get section name
            const section = this.dataset.section;
            
            // Show notification for sections other than dashboard
            if (section && section !== 'dashboard') {
                showNotification(`${section.replace('-', ' ').toUpperCase()} section coming soon!`, 'info');
            }
        });
    });
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.temp-notification');
    if (existing) existing.remove();
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} temp-notification`;
    notification.innerHTML = `
        ${message}
        <button onclick="this.parentElement.remove()">&times;</button>
    `;
    
    // Add to flash messages container
    let container = document.querySelector('.flash-messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 3000);
}
