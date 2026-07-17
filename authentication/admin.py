from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User

admin.site.register(User)


class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Additional Info",
            {"fields": ("phone_number", "role", "created_at", "updated_at")},
        ),
    )
    readonly_fields = ("created_at", "updated_at")
    list_display = (
        "username",
        "email",
        "phone_number",
        "role",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "is_active", "is_staff")
