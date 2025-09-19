// Common JavaScript functions for Timetable Management System

// Global variables
let currentUser = null;

// Initialize common functionality
document.addEventListener('DOMContentLoaded', function() {
    loadCurrentUser();
    setupCommonEventListeners();
});

// Load current user information
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/current-user');
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
        }
    } catch (error) {
        console.error('Error loading current user:', error);
    }
}

// Setup common event listeners
function setupCommonEventListeners() {
    // Handle logout
    window.logout = logout;

    // Handle form submissions with loading state
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.classList.contains('ajax-form')) {
            e.preventDefault();
            handleAjaxForm(form);
        }
    });
}

// Logout function
async function logout() {
    try {
        showLoading(true);
        const response = await fetch('/api/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            window.location.href = '/login';
        } else {
            showAlert('Logout failed', 'danger');
        }
    } catch (error) {
        showAlert('Network error during logout', 'danger');
    } finally {
        showLoading(false);
    }
}

// Show/hide loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        if (show) {
            overlay.classList.remove('d-none');
        } else {
            overlay.classList.add('d-none');
        }
    }
}

// Show alert message
function showAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alertContainer') || createAlertContainer();

    const alertId = 'alert-' + Date.now();
    const alertHTML = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    alertContainer.insertAdjacentHTML('beforeend', alertHTML);

    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, duration);
    }
}

// Create alert container if it doesn't exist
function createAlertContainer() {
    let container = document.getElementById('alertContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'alertContainer';
        container.className = 'alert-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    return container;
}

// Handle AJAX form submissions
async function handleAjaxForm(form) {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;

    try {
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';

        const response = await fetch(form.action, {
            method: form.method || 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            showAlert(result.message || 'Operation completed successfully', 'success');

            // Reset form if successful
            if (form.hasAttribute('data-reset-on-success')) {
                form.reset();
            }

            // Reload page if requested
            if (form.hasAttribute('data-reload-on-success')) {
                setTimeout(() => location.reload(), 1000);
            }

            // Call custom success handler if defined
            const successHandler = form.getAttribute('data-success-handler');
            if (successHandler && window[successHandler]) {
                window[successHandler](result);
            }
        } else {
            showAlert(result.error || 'Operation failed', 'danger');
        }
    } catch (error) {
        console.error('Form submission error:', error);
        showAlert('Network error. Please try again.', 'danger');
    } finally {
        // Restore button state
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// Utility function to format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Utility function to format time
function formatTime(timeString) {
    if (!timeString) return '';
    const [hours, minutes] = timeString.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes));
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Utility function to get day name
function getDayName(dayIndex) {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return days[dayIndex] || '';
}

// Utility function to validate form data
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });

    return isValid;
}

// Utility function to create modal
function createModal(title, body, footerButtons = []) {
    const modalId = 'modal-' + Date.now();

    const modalHTML = `
        <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        ${body}
                    </div>
                    ${footerButtons.length > 0 ? `
                        <div class="modal-footer">
                            ${footerButtons.map(btn => `
                                <button type="button" class="btn ${btn.className || 'btn-secondary'}"
                                        ${btn.dismiss ? 'data-bs-dismiss="modal"' : ''}
                                        ${btn.onclick ? `onclick="${btn.onclick}"` : ''}>
                                    ${btn.text}
                                </button>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);

    const modal = new bootstrap.Modal(document.getElementById(modalId));

    // Clean up modal when hidden
    document.getElementById(modalId).addEventListener('hidden.bs.modal', function() {
        this.remove();
    });

    return modal;
}

// Utility function to confirm action
function confirmAction(message, onConfirm, onCancel = null) {
    const modal = createModal(
        'Confirm Action',
        `<p>${message}</p>`,
        [
            { text: 'Cancel', className: 'btn-secondary', dismiss: true, onclick: onCancel },
            { text: 'Confirm', className: 'btn-primary', onclick: `(${onConfirm.toString()})(); bootstrap.Modal.getInstance(this.closest('.modal')).hide();` }
        ]
    );

    modal.show();
}

// Utility function to show loading in element
function showElementLoading(element, show = true) {
    if (show) {
        element.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</div>';
    }
}

// Utility function to handle API errors
function handleApiError(error, customMessage = null) {
    console.error('API Error:', error);
    showAlert(customMessage || 'An error occurred. Please try again.', 'danger');
}

// Utility function to debounce function calls
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

// Utility function to throttle function calls
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Utility function to copy text to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showAlert('Copied to clipboard', 'success', 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
        showAlert('Failed to copy to clipboard', 'danger');
    }
}

// Utility function to download file
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Export functions for use in other scripts
window.TimetableUtils = {
    showLoading,
    showAlert,
    formatDate,
    formatTime,
    getDayName,
    validateForm,
    createModal,
    confirmAction,
    showElementLoading,
    handleApiError,
    debounce,
    throttle,
    copyToClipboard,
    downloadFile
};