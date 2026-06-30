from django.contrib import admin
from .models import FreeBilling


@admin.register(FreeBilling)
class FreeBillingAdmin(admin.ModelAdmin):
    list_display = ('date', 'guest_name', 'bill_type', 'head', 'bill_status', 'total_bill_amount', 'discount_amount')
    list_filter = ('bill_type', 'head', 'bill_status', 'department')
    search_fields = ('guest_name', 'invoice_no', 'reference')
    date_hierarchy = 'date'
