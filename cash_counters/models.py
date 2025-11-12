from django.db import models
from django.contrib.auth.models import User
from cash_counters.choices import CounterType


class CashCounterLog(models.Model):

    date = models.DateField()
    counter_type = models.CharField(max_length=32, choices=CounterType.choices)
    on_duty_cashier = models.ForeignKey(User, on_delete=models.PROTECT, related_name="cash_logs")
    cash = models.DecimalField(max_digits=12, decimal_places=2)
    handover_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name="cash_handover_logs")

    def __str__(self):
        return f"{self.date} - {self.get_counter_type_display()} - {self.on_duty_cashier}"


class MainCashierReceipt(models.Model):
    date = models.DateField()
    amount_received = models.DecimalField(max_digits=12, decimal_places=2)
    received_from = models.ForeignKey(User, on_delete=models.PROTECT, related_name="amounts_given")
    on_duty_cashier = models.ForeignKey(User, on_delete=models.PROTECT, related_name="amounts_received")

    def __str__(self):
        return f"{self.date} - {self.amount_received}"
