/**
 * Main JavaScript for GitLab Issues Analyzer
 * 
 * Handles common UI interactions and utilities
 */

// Toast Notification System
function showToast(message, variant = 'default', duration = 3000) {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `relative w-full rounded-lg border p-4 mb-2 ${
        variant === 'default' ? 'bg-background text-foreground' :
        variant === 'destructive' ? 'border-destructive/50 text-destructive bg-destructive/10' :
        variant === 'success' ? 'border-green-500/50 bg-green-50 text-green-900' :
        'bg-background text-foreground'
    }`;
    toast.textContent = message;
    
    const closeBtn = document.createElement('button');
    closeBtn.textContent = '×';
    closeBtn.className = 'absolute right-2 top-2 text-current opacity-70 hover:opacity-100';
    closeBtn.onclick = () => toast.remove();
    toast.appendChild(closeBtn);
    
    toastContainer.appendChild(toast);
    
    if (duration > 0) {
        setTimeout(() => toast.remove(), duration);
    }
    
    return toast;
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'fixed top-4 right-4 z-50 w-full max-w-sm space-y-2';
    document.body.appendChild(container);
    return container;
}

// Form Validation Helpers
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('border-destructive');
        } else {
            input.classList.remove('border-destructive');
        }
    });
    
    return isValid;
}

// Loading State Management
function setLoading(elementId, isLoading) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (isLoading) {
        element.classList.add('opacity-50');
        element.disabled = true;
    } else {
        element.classList.remove('opacity-50');
        element.disabled = false;
    }
}

// Utility: Format Date
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Utility: Debounce Function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export for use in other scripts
window.UIUtils = {
    showToast,
    validateForm,
    setLoading,
    formatDate,
    debounce
};
