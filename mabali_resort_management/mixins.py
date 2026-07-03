"""Reusable model mixins for common functionality."""
from django.db import models


class TimeStampedModelMixin(models.Model):
    """Mixin that adds created_at and updated_at timestamp fields to models."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model options."""
        abstract = True


class SoftDeleteModelMixin(models.Model):
    """Mixin that adds soft delete functionality to models."""
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Model options."""
        abstract = True
