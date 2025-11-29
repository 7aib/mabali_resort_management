/**
 * Form Utilities
 * Reusable functions for form handling across the application
 */

/**
 * Initialize form error clearing functionality
 * Automatically clears validation errors when users interact with form fields
 * 
 * Usage: Call formUtils.initErrorClearing() on page load for any form
 * 
 * @param {string} formSelector - Optional CSS selector for specific form (default: 'form')
 * @param {string} cancelBtnSelector - Optional CSS selector for cancel button
 */
const formUtils = {
    /**
     * Initialize error clearing on form fields
     */
    initErrorClearing: function(formSelector = 'form', cancelBtnSelector = null) {
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.querySelector(formSelector);
            if (!form) return;

            // Clear individual field errors when user starts typing
            const formFields = form.querySelectorAll('.form-control, .form-check-input, .form-select');
            formFields.forEach(field => {
                field.addEventListener('input', function() {
                    formUtils.clearFieldError(this);
                });

                // Also clear error on change event (for selects and checkboxes)
                field.addEventListener('change', function() {
                    formUtils.clearFieldError(this);
                });
            });

            // Clear all errors when Cancel button is clicked
            if (cancelBtnSelector) {
                const cancelBtn = document.querySelector(cancelBtnSelector);
                if (cancelBtn) {
                    cancelBtn.addEventListener('click', function() {
                        formUtils.clearAllErrors(form);
                    });
                }
            }
        });
    },

    /**
     * Clear error for a specific field
     * @param {HTMLElement} field - The form field element
     */
    clearFieldError: function(field) {
        // Remove error message for this specific field
        const errorDiv = field.closest('.mb-3, .form-check, .form-group')?.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
        // Remove invalid class from field
        field.classList.remove('is-invalid');
    },

    /**
     * Clear all errors in a form
     * @param {HTMLElement} form - The form element
     */
    clearAllErrors: function(form) {
        // Remove all error messages
        form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
        // Remove all invalid classes
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    },

    /**
     * Add custom validation error to a field
     * @param {HTMLElement} field - The form field element
     * @param {string} message - The error message to display
     */
    addFieldError: function(field, message) {
        // Clear existing error first
        this.clearFieldError(field);
        
        // Add invalid class
        field.classList.add('is-invalid');
        
        // Create and insert error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback d-block';
        errorDiv.textContent = message;
        
        const container = field.closest('.mb-3, .form-check, .form-group');
        if (container) {
            container.appendChild(errorDiv);
        }
    }
};

// Export for use in modules (if using ES6 modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = formUtils;
}
