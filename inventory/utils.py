"""Inventory status transition utilities."""

from django.core.exceptions import ValidationError

from .choices import StockStatusChoices

# Define allowed transitions: {from_status: [allowed_to_statuses]}
STATUS_TRANSITIONS = {
    StockStatusChoices.REQUIRED: [
        StockStatusChoices.ISSUED,
        StockStatusChoices.ORDERED,
        StockStatusChoices.CANCELLED,
    ],
    StockStatusChoices.ISSUED: [],
    StockStatusChoices.ORDERED: [
        StockStatusChoices.PURCHASED,
        StockStatusChoices.CANCELLED,
    ],
    StockStatusChoices.PURCHASED: [],
    StockStatusChoices.CANCELLED: [],
}

# Statuses allowed during creation (no previous status)
CREATION_STATUSES = [StockStatusChoices.REQUIRED, StockStatusChoices.ISSUED]


def get_allowed_transitions(current_status):
    """Return list of statuses that current_status can transition to."""
    return STATUS_TRANSITIONS.get(current_status, [])


def validate_status_transition(old_status, new_status):
    """
    Validate that a status transition is allowed.
    Raises ValidationError if transition is invalid.
    """
    if old_status == new_status:
        return True

    allowed = get_allowed_transitions(old_status)
    if new_status not in allowed:
        old_label = StockStatusChoices(old_status).label if old_status else "None"
        new_label = StockStatusChoices(new_status).label
        allowed_labels = (
            ", ".join(StockStatusChoices(s).label for s in allowed) or "none"
        )
        raise ValidationError(
            'Cannot transition from "%s" to "%s". Allowed: %s'
            % (old_label, new_label, allowed_labels)
        )
    return True


def get_creation_statuses():
    """Return statuses allowed during initial creation."""
    return CREATION_STATUSES
