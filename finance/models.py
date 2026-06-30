from django.db import models
from django.utils import timezone
from .constants import POSPaymentMethodChoices, CounterTypeChoices, TicketRefundReasonChoices
from mabali_resort_management.mixins import TimeStampedModelMixin, SoftDeleteModelMixin


class POS(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    date = models.DateField(default=timezone.now)
    counter_type = models.CharField(max_length=50, choices=CounterTypeChoices.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=POSPaymentMethodChoices.choices)
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'POS entries'

    def __str__(self):
        return f"POS: {self.counter_type} - Rs. {self.amount} on {self.date}"


class TicketRefund(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    date = models.DateField(default=timezone.now)
    no_of_tickets = models.PositiveIntegerField(default=1)
    rate_per_ticket = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount_refunded = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reason = models.CharField(
        max_length=100, choices=TicketRefundReasonChoices.choices,
        default=TicketRefundReasonChoices.WEATHER
    )
    remarks = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Ticket Refunds'

    def __str__(self):
        return 'Refund: %d tickets — Rs. %s on %s' % (
            self.no_of_tickets, self.total_amount_refunded, self.date
        )
