// BagTrack - Client-side JavaScript

// Prevent double form submission
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Processing...';
                
                // Re-enable after 3 seconds in case of error
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.textContent = submitButton.getAttribute('data-original-text') || 'Submit';
                }, 3000);
            }
        });
    });
});

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashes = document.querySelectorAll('.flash');
    
    flashes.forEach(flash => {
        setTimeout(() => {
            flash.style.animation = 'slideOut 0.3s ease-in forwards';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });
});

// Add slideOut animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        to {
            transform: translateY(-20px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Image zoom functionality
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('.production-image, .image-thumbnail');
    
    images.forEach(img => {
        img.style.cursor = 'pointer';
    });
});

// Confirm before logout
const logoutLinks = document.querySelectorAll('.btn-logout');
logoutLinks.forEach(link => {
    link.addEventListener('click', function(e) {
        if (!confirm('Are you sure you want to logout?')) {
            e.preventDefault();
        }
    });
});

// Phone number input formatting
const phoneInputs = document.querySelectorAll('input[type="tel"]');
phoneInputs.forEach(input => {
    input.addEventListener('input', function(e) {
        // Remove non-numeric characters
        this.value = this.value.replace(/\D/g, '');
        
        // Limit to 10 digits
        if (this.value.length > 10) {
            this.value = this.value.slice(0, 10);
        }
    });
});

// Currency input formatting
const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
currencyInputs.forEach(input => {
    input.addEventListener('blur', function() {
        if (this.value) {
            this.value = parseFloat(this.value).toFixed(2);
        }
    });
});

// PWA-like functionality: Prevent pull-to-refresh on mobile
document.addEventListener('touchmove', function(e) {
    if (e.touches.length > 1) {
        e.preventDefault();
    }
}, { passive: false });

let lastTouchY = 0;
let preventPullToRefresh = false;

document.addEventListener('touchstart', function(e) {
    if (e.touches.length !== 1) {
        return;
    }
    lastTouchY = e.touches[0].clientY;
    preventPullToRefresh = window.pageYOffset === 0;
}, { passive: true });

document.addEventListener('touchmove', function(e) {
    const touchY = e.touches[0].clientY;
    const touchYDelta = touchY - lastTouchY;
    lastTouchY = touchY;

    if (preventPullToRefresh) {
        preventPullToRefresh = false;
        if (touchYDelta > 0) {
            e.preventDefault();
            return;
        }
    }
}, { passive: false });

// Add loading indicator for image uploads
const fileInputs = document.querySelectorAll('input[type="file"]');
fileInputs.forEach(input => {
    input.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const fileSize = this.files[0].size / 1024 / 1024; // in MB
            if (fileSize > 16) {
                alert('File size must be less than 16MB');
                this.value = '';
            }
        }
    });
});

console.log('BagTrack initialized ✓');
