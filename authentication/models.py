"""User authentication models."""
from django.contrib.auth.models import AbstractUser
from django.db import models

from mabali_resort_management.mixins import SoftDeleteModelMixin, TimeStampedModelMixin

from .choices import UserRoles


class User(TimeStampedModelMixin, SoftDeleteModelMixin, AbstractUser):
    """Extended user model with role and phone number fields."""
    role = models.CharField(
        max_length=20, choices=UserRoles.choices, default=UserRoles.CUSTOMER
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        null=True,
        help_text="Enter your phone number (e.g. +923001234567)",
    )

    def __str__(self) -> str:
        """Return string representation of user."""
        return f"{self.username} ({self.get_role_display()})"
