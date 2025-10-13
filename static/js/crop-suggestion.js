document.addEventListener('DOMContentLoaded', function() {
    // Form validation and enhancement
    const form = document.querySelector('.suggestion-form');
    const inputs = form.querySelectorAll('input, select');
    
    // Real-time form validation
    inputs.forEach(input => {
        input.addEventListener('input', validateInput);
        input.addEventListener('blur', validateInput);
    });
    
    // Form submission with loading state
    form.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
            return;
        }
        
        // Show loading state
        const submitBtn = form.querySelector('.get-suggestions-btn');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        submitBtn.disabled = true;
        
        // Re-enable after 5 seconds (fallback)
        setTimeout(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }, 5000);
    });
    
    // Initialize tooltips and hints
    initializeHints();
    
    // Animate recommendation cards
    animateRecommendations();
});

function validateInput(e) {
    const input = e.target;
    const value = input.value.trim();
    
    // Remove existing validation classes
    input.classList.remove('valid', 'invalid');
    
    // Validate based on input type
    let isValid = false;
    
    switch (input.name) {
        case 'ph_level':
            isValid = value >= 3 && value <= 12;
            updateHint(input, value, 'pH');
            break;
        case 'organic_matter':
            isValid = value >= 0 && value <= 10;
            updateHint(input, value, 'organic');
            break;
        case 'rainfall':
            isValid = value >= 0 && value <= 5000;
            break;
        case 'temperature':
            isValid = value >= 0 && value <= 50;
            break;
        default:
            isValid = value !== '';
    }
    
    // Add validation class
    if (value !== '') {
        input.classList.add(isValid ? 'valid' : 'invalid');
    }
    
    return isValid;
}

function validateForm() {
    const form = document.querySelector('.suggestion-form');
    const inputs = form.querySelectorAll('input[required], select[required]');
    let isFormValid = true;
    
    inputs.forEach(input => {
        if (!validateInput({ target: input })) {
            isFormValid = false;
        }
    });
    
    if (!isFormValid) {
        showNotification('Please fill in all required fields correctly!', 'error');
    }
    
    return isFormValid;
}

function updateHint(input, value, type) {
    const hint = input.parentNode.querySelector('.input-hint');
    if (!hint) return;
    
    if (type === 'pH') {
        if (value < 6.0) {
            hint.textContent = `${value} - Acidic soil`;
            hint.style.color = '#ef4444';
        } else if (value > 7.5) {
            hint.textContent = `${value} - Alkaline soil`;
            hint.style.color = '#f59e0b';
        } else {
            hint.textContent = `${value} - Optimal range`;
            hint.style.color = '#22c55e';
        }
    } else if (type === 'organic') {
        if (value < 1.0) {
            hint.textContent = `${value}% - Low organic matter`;
            hint.style.color = '#ef4444';
        } else if (value > 3.0) {
            hint.textContent = `${value}% - High organic matter`;
            hint.style.color = '#22c55e';
        } else {
            hint.textContent = `${value}% - Good level`;
            hint.style.color = '#22c55e';
        }
    }
}

function initializeHints() {
    // Season selection helper
    const seasonSelect = document.getElementById('season');
    if (seasonSelect) {
        seasonSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption.value) {
                showNotification(`Selected ${selectedOption.text} season`, 'info');
            }
        });
    }
}

function animateRecommendations() {
    const cards = document.querySelectorAll('.crop-recommendation-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 150);
    });
    
    // Animate suitability bars
    setTimeout(() => {
        const bars = document.querySelectorAll('.suitability-fill');
        bars.forEach((bar, index) => {
            setTimeout(() => {
                const width = bar.style.width;
                bar.style.width = '0%';
                bar.style.transition = 'width 1s ease';
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);
            }, index * 200);
        });
    }, 500);
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

// Enhanced form interactions
document.addEventListener('DOMContentLoaded', function() {
    // Auto-save form data to localStorage
    const form = document.querySelector('.suggestion-form');
    const inputs = form.querySelectorAll('input, select');
    
    // Load saved data
    inputs.forEach(input => {
        const saved = localStorage.getItem(`crop_form_${input.name}`);
        if (saved && !input.value) {
            input.value = saved;
        }
        
        // Save on change
        input.addEventListener('change', function() {
            localStorage.setItem(`crop_form_${this.name}`, this.value);
        });
    });
});

function startGrowingCrop(cropName) {
    window.location.href = `/start_growing/${encodeURIComponent(cropName)}`;
}

// Update the button click handler in your existing code
function displayCropRecommendations(crops) {
    const recommendationsContainer = document.querySelector('.recommendations-container');
    recommendationsContainer.innerHTML = ''; // Clear existing content
    
    crops.forEach(crop => {
        // Create card element (simplified)
        const card = document.createElement('div');
        card.className = 'crop-recommendation-card';
        card.innerHTML = `
            <h3>${crop.name}</h3>
            <p>Suitability: <span class="suitability-fill" style="width: ${crop.suitability}%;"></span></p>
            <button class="btn-success"><i class="fas fa-seedling"></i> Start Growing</button>
        `;
        
        // Add click handler to button
        const startGrowingBtn = card.querySelector('.btn-success');
        startGrowingBtn.onclick = () => startGrowingCrop(crop.name);
        
        recommendationsContainer.appendChild(card);
    });
}
