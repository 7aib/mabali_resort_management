# Form Utilities Documentation

## Overview
The `form-utils.js` library provides reusable JavaScript functions for handling form validation errors across the application.

## Location
`static/js/utils/form-utils.js`

## Features

1. **Auto-clear field errors** - Errors disappear when users start typing
2. **Clear all errors** - Optionally clear all errors when clicking a cancel/back button
3. **Add custom errors** - Programmatically add validation errors to fields
4. **Bootstrap compatible** - Works with Bootstrap form validation classes

## Usage

### Basic Setup

1. **Include the script in your template:**

```django
{% load static %}
{% block extra_js %}
<script src="{% static 'js/utils/form-utils.js' %}"></script>
{% endblock %}
```

2. **Initialize error clearing:**

```javascript
// Basic usage - clears errors on all form fields
formUtils.initErrorClearing();

// With custom form selector
formUtils.initErrorClearing('#myForm');

// With cancel button selector
formUtils.initErrorClearing('form', '.btn-cancel');
```

### Examples

#### Example 1: Simple Form
```django
{% block extra_js %}
<script src="{% static 'js/utils/form-utils.js' %}"></script>
<script>
formUtils.initErrorClearing();
</script>
{% endblock %}
```

#### Example 2: Form with Cancel Button
```django
{% block extra_js %}
<script src="{% static 'js/utils/form-utils.js' %}"></script>
<script>
formUtils.initErrorClearing('form', 'a[href*="back"]');
</script>
{% endblock %}
```

#### Example 3: Add Custom Validation Error
```javascript
const usernameField = document.querySelector('#id_username');
formUtils.addFieldError(usernameField, 'This username is already taken');
```

#### Example 4: Clear All Errors Manually
```javascript
const form = document.querySelector('form');
formUtils.clearAllErrors(form);
```

## API Reference

### `formUtils.initErrorClearing(formSelector, cancelBtnSelector)`
Initialize automatic error clearing for a form.

**Parameters:**
- `formSelector` (string, optional) - CSS selector for the form (default: `'form'`)
- `cancelBtnSelector` (string, optional) - CSS selector for cancel button

**Returns:** void

---

### `formUtils.clearFieldError(field)`
Clear validation error from a specific field.

**Parameters:**
- `field` (HTMLElement) - The form field element

**Returns:** void

---

### `formUtils.clearAllErrors(form)`
Clear all validation errors in a form.

**Parameters:**
- `form` (HTMLElement) - The form element

**Returns:** void

---

### `formUtils.addFieldError(field, message)`
Add a custom validation error to a field.

**Parameters:**
- `field` (HTMLElement) - The form field element
- `message` (string) - The error message to display

**Returns:** void

## Integration with Django Forms

The utility automatically detects and clears Bootstrap validation classes:
- `.invalid-feedback` - Error message containers
- `.is-invalid` - Invalid field styling

Works with Django form rendering that includes these classes in error displays.

## Browser Support

- Modern browsers with ES6 support
- Uses optional chaining (`?.`) - requires recent browsers or polyfill

## Notes

- Errors are only cleared visually - server-side validation still occurs on form submission
- Works best with Bootstrap 5 form validation markup
- Can be extended with additional utility functions as needed
