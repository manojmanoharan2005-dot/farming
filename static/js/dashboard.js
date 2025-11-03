document.addEventListener('DOMContentLoaded', function() {
    // Initialize chart
    initializeProfitChart();
    
    // Start real-time updates
    startRealTimeUpdates();
    
    // Sidebar navigation
    initializeSidebarNav();

    // Initialize Govt Schemes button/panel
    initializeGovtSchemes();
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
            const tempEl = document.getElementById('temperature');
            if (tempEl) tempEl.textContent = `${data.temperature}°C`;
            const humEl = document.getElementById('humidity');
            if (humEl) humEl.textContent = `${data.humidity}%`;
            const rainEl = document.getElementById('rain-chance');
            if (rainEl) rainEl.textContent = `${data.rain_chance}%`;
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
            // Remove active class from all items
            navItems.forEach(nav => nav.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Get section name
            const section = this.dataset.section;
            const href = this.getAttribute('href');
            
            // If link is a placeholder (no href or href="#"), prevent navigation and show notification
            if (!href || href === '#') {
                e.preventDefault();
                if (section && section !== 'dashboard') {
                    showNotification(`${section.replace('-', ' ').toUpperCase()} section coming soon!`, 'info');
                }
            }
            // Otherwise let the browser navigate to the real route (do not preventDefault)
        });
    });
}

function initializeGovtSchemes() {
    // prefer a dedicated toggle button so the main link can navigate normally
    const linkBtn = document.getElementById('govtSchemesBtn');       // anchor that should navigate
    const toggleBtn = document.getElementById('govtSchemesToggle'); // small toggle to open panel
    const panel = document.getElementById('govtSchemesPanel');
    const closeBtn = document.getElementById('govtSchemesClose');

    // if no panel or no toggle/link available, bail out gracefully
    if (!panel || (!linkBtn && !toggleBtn)) return;

    // function to open/close panel
    function openPanel() {
        panel.style.display = 'block';
        if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'true');
    }
    function closePanel() {
        panel.style.display = 'none';
        if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'false');
    }
    function togglePanel(e) {
        if (e && typeof e.stopPropagation === 'function') e.stopPropagation();
        const isOpen = panel.style.display === 'block';
        if (isOpen) closePanel(); else openPanel();
    }

    // Attach toggle behavior to the small toggle button if present.
    // We intentionally do NOT intercept clicks on the main linkBtn so it navigates normally.
    if (toggleBtn) {
        toggleBtn.addEventListener('click', togglePanel);
    } else if (linkBtn) {
        // fallback: if no separate toggle exists, clicking the main control should open/close panel
        linkBtn.addEventListener('click', function (e) {
            // if the link has an href that points to our static page, allow navigation on plain click.
            // If user holds ctrl/meta/shift or middle-click, navigation will happen normally.
            // To provide panel access when fallback is used, open panel only on Alt+click
            if (e.altKey) {
                e.preventDefault();
                togglePanel(e);
            }
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', function (e) { e.stopPropagation(); closePanel(); });
    }

    // Close panel when clicking outside
    document.addEventListener('click', function (ev) {
        const target = ev.target;
        if (!panel.contains(target) && !(toggleBtn && toggleBtn.contains(target)) && !(linkBtn && linkBtn.contains(target)) && panel.style.display === 'block') {
            closePanel();
        }
    });

    // Allow Esc to close
    document.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape' && panel.style.display === 'block') closePanel();
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
