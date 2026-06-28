"""Reservations app models."""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from authentication.models import User
from mabali_resort_management.mixins import TimeStampedModelMixin, SoftDeleteModelMixin
from .choices import (
    RoomCategoryChoices, PaymentMethodChoices, PaymentTypeChoices,
    ReservationStatusChoices, BankChoices,
)


class Room(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """Reference table for rooms, huts, suites, and honeymoon rooms."""

    name = models.CharField(max_length=80, unique=True)
    category = models.CharField(max_length=20, choices=RoomCategoryChoices.choices)
    rate_per_night = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Reservation(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    """A single reservation booking with advance and final payment tracking."""

    # Guest info
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    phone_number = models.CharField(max_length=15, blank=True, default='')
    guest_name = models.CharField(max_length=150, blank=True, default='')

    # Occupancy
    no_of_adults = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    no_of_kids = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])

    # Room
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reservations')

    # Dates
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    nights = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])

    # Rates
    rate_per_night = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    # Advance payment
    advance_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    advance_date = models.DateField(null=True, blank=True)
    advance_bank = models.CharField(
        max_length=30, choices=BankChoices.choices, blank=True, default=''
    )

    # Final payment
    amount_received = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    payment_type = models.CharField(
        max_length=10, choices=PaymentTypeChoices.choices, default=PaymentTypeChoices.ADVANCE
    )
    payment_method = models.CharField(
        max_length=10, choices=PaymentMethodChoices.choices, blank=True, default=''
    )

    # Status
    status = models.CharField(
        max_length=20, choices=ReservationStatusChoices.choices,
        default=ReservationStatusChoices.CONFIRMED
    )

    # Meta
    remarks = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_reservations'
    )

    class Meta:
        ordering = ['-check_in_date', '-created_at']
        verbose_name_plural = 'Reservations'

    def __str__(self) -> str:
        return f"{self.guest_name} — {self.room.name} ({self.check_in_date})"

    @property
    def total_cost(self):
        return self.rate_per_night * self.nights - self.discount

    @property
    def balance_due(self):
        return self.total_cost - self.advance_amount - self.amount_received
