document.addEventListener('DOMContentLoaded', function() {
    // Add form animations (match actual template class names)
    const formSections = document.querySelectorAll('.fertilizer-form-section');
    formSections.forEach((section, index) => {
        section.style.animationDelay = `${index * 0.1}s`;
        section.classList.add('animate-slide-in');
    });

    // Add recommendation card animations (match actual template class names)
    const recommendationCards = document.querySelectorAll('.fertilizer-recommendation-card');
    recommendationCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.2}s`;
        card.classList.add('animate-scale-in');
    });

    // Update current date
    const dateElement = document.querySelector('.current-date');
    if (dateElement) {
        const today = new Date();
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        dateElement.textContent = today.toLocaleDateString('en-US', options);
    }

    // Form validation (match actual form class)
    const form = document.querySelector('.fertilizer-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const inputs = form.querySelectorAll('input[required], select[required]');
            let isValid = true;

            inputs.forEach(input => {
                // For numeric inputs, allow 0 as valid but ensure not empty
                if (input.type === 'number') {
                    if (input.value === '' || input.value === null) {
                        input.classList.add('invalid');
                        isValid = false;
                    } else {
                        input.classList.remove('invalid');
                        input.classList.add('valid');
                    }
                } else {
                    if (!input.value.trim()) {
                        input.classList.add('invalid');
                        isValid = false;
                    } else {
                        input.classList.remove('invalid');
                        input.classList.add('valid');
                    }
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields');
            }
        });
    }

    // Buy Now button handler: send fertilizer details to backend SQLite endpoint
    function handleBuyNowClick(event) {
        const btn = event.currentTarget;
        // prevent double clicks if already added
        if (btn.dataset.added === 'true') return;

        const fertilizer = {
            name: btn.dataset.name || '',
            cost: parseFloat(btn.dataset.cost) || 0,
            yield_increase: btn.dataset.yield || '',
            application_time: btn.dataset.time || '',
            // new fields:
            selected_for: btn.dataset.crop || '',
            suitability: parseFloat(btn.dataset.suitability) || null
        };

        // optimistic UI lock
        btn.disabled = true;
        const originalText = btn.textContent;
        btn.textContent = 'Adding...';

        const payload = JSON.stringify(fertilizer);
        console.debug('Adding fertilizer to dashboard:', payload);

        fetch('/add_dashboard_fertilizer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: payload
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    const message = `Server returned ${response.status} ${response.statusText}: ${text.substring(0, 500)}`;
                    throw new Error(message);
                });
            }
            return response.json().catch(err => {
                throw new Error('Response JSON parse error: ' + err.message);
            });
        })
        .then(data => {
            if (data && data.status === 'success') {
                alert('Added to Dashboard ✅');
                btn.textContent = 'Added';
                btn.dataset.added = 'true';
                btn.classList.add('added');

                // update inline badge in the same card
                // find nearest .fertilizer-recommendation-card ancestor
                const card = btn.closest('.fertilizer-recommendation-card');
                if (card) {
                    const badge = card.querySelector('.added-badge');
                    if (badge) {
                        const crop = data.fertilizer && data.fertilizer.selected_for ? data.fertilizer.selected_for : fertilizer.selected_for;
                        const suit = (data.fertilizer && typeof data.fertilizer.suitability !== 'undefined') ? data.fertilizer.suitability : fertilizer.suitability;
                        badge.textContent = `Added for ${crop}${suit ? ' (' + suit + '%)' : ''}`;
                        badge.style.display = 'inline-block';
                    }

                    // NEW: update the "Recommended For" detail row inside the card
                    const selElem = card.querySelector('.fertilizer-selected-for');
                    if (selElem) {
                        const crop = data.fertilizer && data.fertilizer.selected_for ? data.fertilizer.selected_for : fertilizer.selected_for;
                        const suit = (data.fertilizer && typeof data.fertilizer.suitability !== 'undefined') ? data.fertilizer.suitability : fertilizer.suitability;
                        selElem.textContent = crop + (suit ? ' (' + suit + '%)' : '');
                    }

                    // NEW: update small crop labels near Yield and Application Time
                    const cropLabelYield = card.querySelector('.fertilizer-detail-crop-yield');
                    const cropLabelTime  = card.querySelector('.fertilizer-detail-crop-time');
                    if (cropLabelYield || cropLabelTime) {
                        const crop = data.fertilizer && data.fertilizer.selected_for ? data.fertilizer.selected_for : fertilizer.selected_for;
                        if (cropLabelYield) cropLabelYield.textContent = crop ? 'For ' + crop : '';
                        if (cropLabelTime)  cropLabelTime.textContent  = crop ? 'For ' + crop : '';
                    }
                }
            } else {
                throw new Error((data && data.error) ? data.error : 'Save failed');
            }
        })
        .catch(err => {
            console.error('Error adding fertilizer to dashboard:', err);
            alert('Could not add to Dashboard. Try again.\n\n' + err.message);
            btn.disabled = false;
            btn.textContent = originalText;
        });
    }

    // Attach handlers to existing buy-now buttons (if any)
    const buyNowButtons = document.querySelectorAll('.buy-now-btn');
    buyNowButtons.forEach(btn => {
        btn.addEventListener('click', handleBuyNowClick);
    });

    // Attach handlers to "Add Me" buttons (new) - reuses same save handler
    const addMeButtons = document.querySelectorAll('.add-me-btn');
    addMeButtons.forEach(btn => {
        btn.addEventListener('click', handleBuyNowClick);
    });
});
