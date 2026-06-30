from django.db import models
from django.utils import timezone
from .constants import POSPaymentMethodChoices, CounterTypeChoices
from mabali_resort_management.mixins import TimeStampedModelMixin, SoftDeleteModelMixin


class POS(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    date = models.DateField(default=timezone.localdate)
    counter_type = models.CharField(max_length=50, choices=CounterTypeChoices.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=POSPaymentMethodChoices.choices)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'POS entries'

    def __str__(self):
        return f"POS: {self.counter_type} - Rs. {self.amount} on {self.date}"
