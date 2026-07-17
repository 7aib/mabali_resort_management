from django.contrib import admin

from .models import POS


@admin.register(POS)
class POSAdmin(admin.ModelAdmin):
    list_display = ("date", "counter_type", "amount", "payment_method")
    list_filter = ("counter_type", "payment_method", "date")
    search_fields = ("remarks",)
    date_hierarchy = "date"
