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
});
