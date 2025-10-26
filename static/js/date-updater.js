/**
 * Date Updater - Updates the current date display dynamically
 * This script runs on page load and updates the date daily
 */

document.addEventListener('DOMContentLoaded', function() {
    updateCurrentDate();
    
    // Update date every minute to catch day changes
    setInterval(updateCurrentDate, 60000);
    
    // Also update at midnight to ensure the date changes
    scheduleNextDayUpdate();
});

function updateCurrentDate() {
    const dateElement = document.querySelector('.current-date');
    if (!dateElement) return;
    
    const today = new Date();
    const formattedDate = formatDate(today);
    dateElement.textContent = formattedDate;
}

function formatDate(date) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

function scheduleNextDayUpdate() {
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    
    const timeUntilMidnight = tomorrow - now;
    
    setTimeout(function() {
        updateCurrentDate();
        // Reschedule for the next day
        scheduleNextDayUpdate();
    }, timeUntilMidnight);
}
