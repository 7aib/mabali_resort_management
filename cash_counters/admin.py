from django.contrib import admin
from .models import EntryCounterForm, EntryTransaction, CashHandover, CashRegister, TicketRefund


@admin.register(EntryCounterForm)
class EntryCounterFormAdmin(admin.ModelAdmin):
    list_display = ('customer', 'location', 'no_of_persons', 'no_of_kids', 'visit_type', 'gate', 'status', 'created_at')
    list_filter = ('visit_type', 'gate', 'status', 'location')
    search_fields = ('customer__username', 'customer__first_name', 'customer__last_name')
    raw_id_fields = ('customer',)


@admin.register(EntryTransaction)
class EntryTransactionAdmin(admin.ModelAdmin):
    list_display = ('entry_form', 'amount', 'payment_method')
    list_filter = ('payment_method',)
    raw_id_fields = ('entry_form',)


@admin.register(CashHandover)
class CashHandoverAdmin(admin.ModelAdmin):
    list_display = ('date', 'counter_type', 'cashier', 'cash_amount', 'handover_to')
    list_filter = ('counter_type', 'date')
    search_fields = ('cashier__username', 'handover_to__username')
    raw_id_fields = ('cashier', 'handover_to')


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ('date', 'counter_type', 'amount_received', 'received_from', 'on_duty_cashier')
    list_filter = ('counter_type', 'date')
    search_fields = ('received_from__username', 'on_duty_cashier__username')
    raw_id_fields = ('received_from', 'on_duty_cashier')


@admin.register(TicketRefund)
class TicketRefundAdmin(admin.ModelAdmin):
    list_display = ('date', 'no_of_tickets', 'rate_per_ticket', 'total_amount_refunded', 'reason')
    list_filter = ('reason', 'date')
    search_fields = ('remarks',)
    date_hierarchy = 'date'
