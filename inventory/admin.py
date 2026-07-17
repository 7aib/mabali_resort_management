from django.contrib import admin

from .models import (
    AmbulanceLog,
    AmmoTransactionLog,
    FuelTransactionLog,
    GeneratorLog,
    InventoryItem,
)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "stock_quantity",
        "unit",
        "supplier",
        "created_at",
    )
    list_filter = ("category",)
    search_fields = ("name", "supplier", "notes")


@admin.register(FuelTransactionLog)
class FuelTransactionLogAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "inventory_item",
        "transaction_status",
        "quantity",
        "amount",
        "created_by",
    )
    list_filter = ("transaction_status", "date")
    search_fields = ("inventory_item__name", "notes")
    raw_id_fields = ("inventory_item", "issued_to", "created_by")


@admin.register(AmmoTransactionLog)
class AmmoTransactionLogAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "inventory_item",
        "transaction_status",
        "bullet_quantity",
        "payment",
        "created_by",
    )
    list_filter = ("transaction_status", "payment", "date")
    search_fields = ("inventory_item__name", "notes")
    raw_id_fields = ("inventory_item", "created_by")


@admin.register(GeneratorLog)
class GeneratorLogAdmin(admin.ModelAdmin):
    list_display = (
        "generator",
        "run_hours",
        "fuel_used_liters",
        "created_by",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("generator__name", "notes")
    raw_id_fields = ("generator", "created_by")


@admin.register(AmbulanceLog)
class AmbulanceLogAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "patient_name",
        "ambulance",
        "hospital",
        "kms_travelled",
        "driver",
    )
    list_filter = ("hospital", "date")
    search_fields = ("patient_name", "ambulance__name", "notes")
    raw_id_fields = ("ambulance", "driver")
