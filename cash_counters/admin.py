from django.contrib import admin
from .models import CashCounterLog, MainCashierReceipt


@admin.site.register(CashCounterLog)
class CashCounterLogAdmin(admin.ModelAdmin):
    list_display = ("date", "counter_type", "on_duty_cashier", "cash", "handover_to")
    list_filter = ("counter_type", "date", "on_duty_cashier")
    search_fields = ("on_duty_cashier__username", "handover_to__username")

@admin.site.register(MainCashierReceipt)
class MainCashierReceiptAdmin(admin.ModelAdmin):
    list_display = ("date", "amount_received", "received_from", "on_duty_cashier")
    list_filter = ("date", "received_from", "on_duty_cashier")
    search_fields = ("received_from__username", "on_duty_cashier__username")
