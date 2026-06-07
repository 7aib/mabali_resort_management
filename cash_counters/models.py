from django.db import models
from django.conf import settings
from .constants import CitiesChoices, PaymentMethodChoices, VisitTypeChoices, GateChoices, StatusChoices
from mabali_resort_management.mixins import TimeStampedModelMixin, SoftDeleteModelMixin

class EntryCounterForm(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='entries')
    location = models.CharField(max_length=50, choices=CitiesChoices.choices, default=CitiesChoices.OTHER)
    no_of_persons = models.PositiveIntegerField(default=1)
    no_of_kids = models.PositiveIntegerField(default=0)
    visit_type = models.CharField(max_length=50, choices=VisitTypeChoices.choices, default=VisitTypeChoices.PAID)
    gate = models.CharField(max_length=50, choices=GateChoices.choices, default=GateChoices.MAIN)
    status = models.CharField(max_length=10, choices=StatusChoices.choices)

    def __str__(self):
        return f"Entry: {self.customer.get_full_name() or self.customer.username} - {self.visit_type} at {self.created_at.date()}"

class EntryTransaction(TimeStampedModelMixin, SoftDeleteModelMixin, models.Model):
    
    entry_form = models.OneToOneField(EntryCounterForm, on_delete=models.CASCADE, related_name='transaction')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethodChoices.choices, default=PaymentMethodChoices.CASH)
    

    def __str__(self):
        return f"Tx: {self.entry_form.customer.get_full_name() or self.entry_form.customer.username} - {self.amount} ({self.payment_method})"