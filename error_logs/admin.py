from django.contrib import admin
from .models import ErrorLog


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('level', 'short_message', 'url', 'user_display', 'created_at')
    list_filter = ('level', 'created_at')
    search_fields = ('message', 'exception_type', 'url', 'user_display')
    readonly_fields = (
        'level', 'logger_name', 'message', 'exception_type', 'exception_traceback',
        'url', 'method', 'query_string', 'ip_address', 'user_agent',
        'user_id', 'user_display', 'created_at',
    )
    date_hierarchy = 'created_at'

    def short_message(self, obj):
        return (obj.message[:100] + '…') if len(obj.message) > 100 else obj.message
    short_message.short_description = 'Message'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
