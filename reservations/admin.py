from django.contrib import admin

from .models import Reservation, Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "rate_per_night", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name",)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "guest_name",
        "room",
        "check_in_date",
        "check_out_date",
        "nights",
        "advance_amount",
        "amount_received",
        "status",
    )
    list_filter = ("status", "room__category", "payment_type")
    search_fields = ("guest_name", "phone_number")
    raw_id_fields = ("customer", "room", "created_by")
