document.addEventListener('DOMContentLoaded', function() {
    // Add form animations
    const formSections = document.querySelectorAll('.form-section');
    formSections.forEach((section, index) => {
        section.style.animationDelay = `${index * 0.1}s`;
        section.classList.add('animate-slide-in');
    });

    // Add recommendation card animations
    const recommendationCards = document.querySelectorAll('.crop-recommendation-card');
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

    // Form validation
    const form = document.querySelector('.suggestion-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const inputs = form.querySelectorAll('input[required], select[required]');
            let isValid = true;

            inputs.forEach(input => {
                if (!input.value.trim()) {
                    input.classList.add('invalid');
                    isValid = false;
                } else {
                    input.classList.remove('invalid');
                    input.classList.add('valid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields');
            }
        });
    }
});
